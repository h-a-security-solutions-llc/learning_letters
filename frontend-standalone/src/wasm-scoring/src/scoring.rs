//! Main scoring logic for character recognition
//!
//! Implements the scoring algorithm that compares user drawings against reference images.

use crate::image_ops::{
    distance_transform_edt, binary_dilation, skeletonize, bridge_gaps, prune_branches
};
use crate::WasmScoringResult;
use crate::ScoringResult;
use image::{DynamicImage, GrayImage, ImageBuffer, Luma, ImageEncoder};
use image::codecs::png::PngEncoder;
use rusttype::{Font, Scale, point};
use std::io::Cursor;

const TARGET_SIZE: u32 = 128;
const THRESHOLD: u8 = 200;

/// Main scoring function
pub fn score_drawing_internal(
    image_data: &[u8],
    character: char,
    font_data: &[u8],
) -> Result<WasmScoringResult, String> {
    // Decode the user's drawing
    let drawn_image = image::load_from_memory(image_data)
        .map_err(|e| format!("Failed to decode image: {}", e))?;

    // Generate reference image
    let reference_image = generate_reference_gray(character, font_data, 200)?;

    // Process both images
    let drawn_processed = extract_and_center_character(&drawn_image.to_luma8());
    let reference_processed = extract_and_center_character(&reference_image);

    // Calculate scores
    let coverage = calculate_coverage_score(&drawn_processed, &reference_processed);
    let accuracy = calculate_accuracy_score(&drawn_processed, &reference_processed);
    let similarity = calculate_stroke_similarity(&drawn_processed, &reference_processed);

    // Combined score with weights: 35% coverage, 35% accuracy, 30% similarity
    let combined_score = coverage * 0.35 + accuracy * 0.35 + similarity * 0.30;
    let percentage_score = (combined_score * 100.0).min(100.0).max(0.0) as u8;

    // Star rating
    let (stars, feedback) = get_star_rating(percentage_score);

    // Generate reference image PNG for display
    let reference_png = encode_grayscale_to_png(&reference_image)?;

    Ok(WasmScoringResult {
        inner: ScoringResult {
            score: percentage_score,
            stars,
            feedback,
            coverage: (coverage * 100.0).round(),
            accuracy: (accuracy * 100.0).round(),
            similarity: (similarity * 100.0).round(),
        },
        reference_image: reference_png,
    })
}

/// Generate a reference image as PNG bytes
pub fn generate_reference_image_internal(
    character: char,
    font_data: &[u8],
    size: u32,
) -> Result<Vec<u8>, String> {
    let gray = generate_reference_gray(character, font_data, size)?;
    encode_grayscale_to_png(&gray)
}

fn generate_reference_gray(character: char, font_data: &[u8], size: u32) -> Result<GrayImage, String> {
    let font = Font::try_from_bytes(font_data)
        .ok_or("Failed to parse font data")?;

    let mut img: GrayImage = ImageBuffer::from_pixel(size, size, Luma([255u8]));

    let font_size = size as f32 * 0.75;
    let scale = Scale::uniform(font_size);

    // Get glyph metrics for centering
    let glyph = font.glyph(character).scaled(scale);
    let h_metrics = glyph.h_metrics();

    let glyph = glyph.positioned(point(0.0, 0.0));

    if let Some(bb) = glyph.pixel_bounding_box() {
        let glyph_width = bb.max.x - bb.min.x;
        let glyph_height = bb.max.y - bb.min.y;

        // Center the glyph
        let x_offset = ((size as i32 - glyph_width) / 2) - bb.min.x;
        let y_offset = ((size as i32 - glyph_height) / 2) - bb.min.y;

        // Reposition glyph centered
        let glyph = font.glyph(character)
            .scaled(scale)
            .positioned(point(x_offset as f32, y_offset as f32 + font_size * 0.8));

        // Draw the glyph
        if let Some(bb) = glyph.pixel_bounding_box() {
            glyph.draw(|x, y, v| {
                let px = x as i32 + bb.min.x;
                let py = y as i32 + bb.min.y;

                if px >= 0 && px < size as i32 && py >= 0 && py < size as i32 {
                    let intensity = (255.0 * (1.0 - v)) as u8;
                    img.put_pixel(px as u32, py as u32, Luma([intensity]));
                }
            });
        }
    }

    Ok(img)
}

fn encode_grayscale_to_png(img: &GrayImage) -> Result<Vec<u8>, String> {
    let mut buffer = Vec::new();
    let encoder = PngEncoder::new(&mut buffer);
    encoder.write_image(
        img.as_raw(),
        img.width(),
        img.height(),
        image::ExtendedColorType::L8,
    ).map_err(|e| format!("Failed to encode PNG: {}", e))?;
    Ok(buffer)
}

/// Extract the drawn character, center it, and normalize to target size
fn extract_and_center_character(image: &GrayImage) -> Vec<f32> {
    let (width, height) = image.dimensions();
    let mut drawn_mask = vec![false; (width * height) as usize];

    // Find drawn pixels (dark pixels)
    for y in 0..height {
        for x in 0..width {
            let pixel = image.get_pixel(x, y).0[0];
            drawn_mask[(y * width + x) as usize] = pixel < THRESHOLD;
        }
    }

    // Find bounding box
    let mut min_x = width;
    let mut max_x = 0;
    let mut min_y = height;
    let mut max_y = 0;
    let mut has_content = false;

    for y in 0..height {
        for x in 0..width {
            if drawn_mask[(y * width + x) as usize] {
                has_content = true;
                min_x = min_x.min(x);
                max_x = max_x.max(x);
                min_y = min_y.min(y);
                max_y = max_y.max(y);
            }
        }
    }

    if !has_content {
        return vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize];
    }

    // Extract region
    let region_width = max_x - min_x + 1;
    let region_height = max_y - min_y + 1;

    // Calculate scale to fit in target size with padding
    let padding = 0.1;
    let available_size = (TARGET_SIZE as f32 * (1.0 - 2.0 * padding)) as u32;
    let scale = (available_size as f32 / region_width as f32)
        .min(available_size as f32 / region_height as f32);

    let new_width = ((region_width as f32 * scale) as u32).max(1);
    let new_height = ((region_height as f32 * scale) as u32).max(1);

    // Create output
    let mut output = vec![1.0f32; (TARGET_SIZE * TARGET_SIZE) as usize];

    let x_offset = (TARGET_SIZE - new_width) / 2;
    let y_offset = (TARGET_SIZE - new_height) / 2;

    // Resample to target size
    for ty in 0..new_height {
        for tx in 0..new_width {
            let src_x = min_x + (tx as f32 / scale) as u32;
            let src_y = min_y + (ty as f32 / scale) as u32;

            if src_x < width && src_y < height {
                let src_pixel = image.get_pixel(src_x, src_y).0[0];
                let dst_idx = ((y_offset + ty) * TARGET_SIZE + (x_offset + tx)) as usize;
                output[dst_idx] = src_pixel as f32 / 255.0;
            }
        }
    }

    output
}

/// Normalize line thickness using skeleton extraction
fn normalize_line_thickness(binary: &[bool], width: usize, height: usize, target_thickness: u32, apply_sanding: bool) -> Vec<bool> {
    if !binary.iter().any(|&x| x) {
        return binary.to_vec();
    }

    let skeleton = if apply_sanding {
        let mut skel = skeletonize(binary, width, height);
        bridge_gaps(&mut skel, width, height, 10);
        prune_branches(&mut skel, width, height, 8, 0.15);
        skel
    } else {
        skeletonize(binary, width, height)
    };

    if target_thickness > 1 {
        // Use distance transform for smooth stroke reconstruction
        if !skeleton.iter().any(|&x| x) {
            return binary.to_vec();
        }

        let dist = distance_transform_edt(&skeleton, width, height);
        let threshold = target_thickness as f32 / 2.0;

        dist.iter().map(|&d| d <= threshold).collect()
    } else {
        skeleton
    }
}

/// Calculate coverage score: how much of the reference is covered
fn calculate_coverage_score(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;
    let tolerance = 4;

    // Convert to binary
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < 0.5).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < 0.5).collect();

    // Normalize line thickness
    let drawn_norm = normalize_line_thickness(&drawn_binary, size, size, 5, true);
    let reference_norm = normalize_line_thickness(&reference_binary, size, size, 5, false);

    let ref_pixels: u32 = reference_norm.iter().filter(|&&x| x).count() as u32;
    if ref_pixels == 0 {
        return 0.0;
    }

    let drawn_pixels: u32 = drawn_norm.iter().filter(|&&x| x).count() as u32;
    if drawn_pixels == 0 {
        return 0.0;
    }

    // Distance from each pixel to nearest drawn pixel
    let drawn_dist = distance_transform_edt(&drawn_norm, size, size);

    // Count reference pixels that are covered (within tolerance of drawn pixels)
    let covered: u32 = reference_norm.iter()
        .zip(drawn_dist.iter())
        .filter(|(&is_ref, &dist)| is_ref && dist <= tolerance as f32)
        .count() as u32;

    (covered as f32 / ref_pixels as f32).min(1.0)
}

/// Calculate accuracy score: how accurate is the drawing (staying on the lines)
fn calculate_accuracy_score(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;

    // Convert to binary
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < 0.5).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < 0.5).collect();

    // Normalize with sanding for drawn, without for reference
    let drawn_norm = normalize_line_thickness(&drawn_binary, size, size, 5, true);
    let reference_norm = normalize_line_thickness(&reference_binary, size, size, 5, false);

    let drawn_pixels: u32 = drawn_norm.iter().filter(|&&x| x).count() as u32;
    if drawn_pixels == 0 {
        return 0.0;
    }

    // Dilate reference to create acceptable zone
    let reference_zone = binary_dilation(&reference_norm, size, size, 5);

    // Count drawn pixels within acceptable zone
    let within_bounds: u32 = drawn_norm.iter()
        .zip(reference_zone.iter())
        .filter(|(&is_drawn, &is_zone)| is_drawn && is_zone)
        .count() as u32;

    (within_bounds as f32 / drawn_pixels as f32).min(1.0)
}

/// Calculate stroke similarity using IoU and Chamfer distance
fn calculate_stroke_similarity(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;

    // Convert to binary
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < 0.5).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < 0.5).collect();

    // Normalize both
    let drawn_norm = normalize_line_thickness(&drawn_binary, size, size, 5, true);
    let ref_norm = normalize_line_thickness(&reference_binary, size, size, 5, false);

    let drawn_pixels: u32 = drawn_norm.iter().filter(|&&x| x).count() as u32;
    let ref_pixels: u32 = ref_norm.iter().filter(|&&x| x).count() as u32;

    if drawn_pixels == 0 || ref_pixels == 0 {
        return 0.0;
    }

    // IoU (40% weight)
    let intersection: u32 = drawn_norm.iter()
        .zip(ref_norm.iter())
        .filter(|(&d, &r)| d && r)
        .count() as u32;
    let union: u32 = drawn_norm.iter()
        .zip(ref_norm.iter())
        .filter(|(&d, &r)| d || r)
        .count() as u32;
    let iou = intersection as f32 / (union as f32 + 1e-8);

    // Chamfer distance (60% weight)
    let ref_dist = distance_transform_edt(&ref_norm, size, size);
    let drawn_dist = distance_transform_edt(&drawn_norm, size, size);

    // Average distance from drawn to reference
    let mut drawn_to_ref_sum = 0.0f32;
    let mut drawn_to_ref_count = 0u32;
    for (i, &is_drawn) in drawn_norm.iter().enumerate() {
        if is_drawn {
            drawn_to_ref_sum += ref_dist[i];
            drawn_to_ref_count += 1;
        }
    }
    let drawn_to_ref = if drawn_to_ref_count > 0 {
        drawn_to_ref_sum / drawn_to_ref_count as f32
    } else {
        0.0
    };

    // Average distance from reference to drawn
    let mut ref_to_drawn_sum = 0.0f32;
    let mut ref_to_drawn_count = 0u32;
    for (i, &is_ref) in ref_norm.iter().enumerate() {
        if is_ref {
            ref_to_drawn_sum += drawn_dist[i];
            ref_to_drawn_count += 1;
        }
    }
    let ref_to_drawn = if ref_to_drawn_count > 0 {
        ref_to_drawn_sum / ref_to_drawn_count as f32
    } else {
        0.0
    };

    // Symmetric Chamfer distance
    let chamfer_dist = (drawn_to_ref + ref_to_drawn) / 2.0;

    // Convert to similarity score
    let max_dist = 20.0;
    let chamfer_score = (-chamfer_dist / (max_dist / 3.0)).exp();

    // Combine
    let similarity = iou * 0.4 + chamfer_score * 0.6;
    similarity.min(1.0).max(0.0)
}

fn get_star_rating(score: u8) -> (u8, String) {
    match score {
        80..=100 => (5, "Amazing! Perfect!".to_string()),
        65..=79 => (4, "Great job!".to_string()),
        50..=64 => (3, "Good work!".to_string()),
        30..=49 => (2, "Nice try!".to_string()),
        _ => (1, "Keep practicing!".to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_star_rating_5_stars() {
        let (stars, feedback) = get_star_rating(100);
        assert_eq!(stars, 5);
        assert_eq!(feedback, "Amazing! Perfect!");

        let (stars, feedback) = get_star_rating(80);
        assert_eq!(stars, 5);
        assert_eq!(feedback, "Amazing! Perfect!");
    }

    #[test]
    fn test_get_star_rating_4_stars() {
        let (stars, feedback) = get_star_rating(79);
        assert_eq!(stars, 4);
        assert_eq!(feedback, "Great job!");

        let (stars, feedback) = get_star_rating(65);
        assert_eq!(stars, 4);
        assert_eq!(feedback, "Great job!");
    }

    #[test]
    fn test_get_star_rating_3_stars() {
        let (stars, feedback) = get_star_rating(64);
        assert_eq!(stars, 3);
        assert_eq!(feedback, "Good work!");

        let (stars, feedback) = get_star_rating(50);
        assert_eq!(stars, 3);
        assert_eq!(feedback, "Good work!");
    }

    #[test]
    fn test_get_star_rating_2_stars() {
        let (stars, feedback) = get_star_rating(49);
        assert_eq!(stars, 2);
        assert_eq!(feedback, "Nice try!");

        let (stars, feedback) = get_star_rating(30);
        assert_eq!(stars, 2);
        assert_eq!(feedback, "Nice try!");
    }

    #[test]
    fn test_get_star_rating_1_star() {
        let (stars, feedback) = get_star_rating(29);
        assert_eq!(stars, 1);
        assert_eq!(feedback, "Keep practicing!");

        let (stars, feedback) = get_star_rating(0);
        assert_eq!(stars, 1);
        assert_eq!(feedback, "Keep practicing!");
    }

    #[test]
    fn test_extract_and_center_character_empty() {
        // All white image (no drawing)
        let img = GrayImage::from_pixel(100, 100, Luma([255u8]));
        let result = extract_and_center_character(&img);

        // Should return all 1.0 (white)
        assert_eq!(result.len(), (TARGET_SIZE * TARGET_SIZE) as usize);
        assert!(result.iter().all(|&v| v == 1.0));
    }

    #[test]
    fn test_extract_and_center_character_with_content() {
        // Create image with a black square in the center
        let mut img = GrayImage::from_pixel(100, 100, Luma([255u8]));
        for y in 40..60 {
            for x in 40..60 {
                img.put_pixel(x, y, Luma([0u8]));
            }
        }

        let result = extract_and_center_character(&img);

        // Should have some dark pixels (< 0.5)
        let dark_count = result.iter().filter(|&&v| v < 0.5).count();
        assert!(dark_count > 0);
    }

    #[test]
    fn test_normalize_line_thickness_empty() {
        let binary = vec![false; 100];
        let result = normalize_line_thickness(&binary, 10, 10, 5, false);

        // Should remain empty
        assert!(result.iter().all(|&x| !x));
    }

    #[test]
    fn test_normalize_line_thickness_with_content() {
        // Create a thick horizontal line
        let mut binary = vec![false; 100];
        for y in 3..7 {
            for x in 2..8 {
                binary[y * 10 + x] = true;
            }
        }

        let result = normalize_line_thickness(&binary, 10, 10, 3, false);

        // Should have fewer true pixels than original (thinned)
        let original_count: usize = binary.iter().filter(|&&x| x).count();
        let result_count: usize = result.iter().filter(|&&x| x).count();

        // The line should be thinner but still present
        assert!(result_count > 0);
        assert!(result_count <= original_count);
    }

    #[test]
    fn test_calculate_coverage_score_perfect() {
        // Identical images should give high coverage
        let image: Vec<f32> = (0..TARGET_SIZE * TARGET_SIZE)
            .map(|i| if i % 10 == 0 { 0.0 } else { 1.0 })
            .collect();

        let score = calculate_coverage_score(&image, &image);

        // Should be very high (close to 1.0)
        assert!(score > 0.9);
    }

    #[test]
    fn test_calculate_coverage_score_empty_drawn() {
        let drawn: Vec<f32> = vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize]; // all white
        let reference: Vec<f32> = (0..TARGET_SIZE * TARGET_SIZE)
            .map(|i| if i % 10 == 0 { 0.0 } else { 1.0 })
            .collect();

        let score = calculate_coverage_score(&drawn, &reference);

        // Should be 0 (nothing drawn)
        assert_eq!(score, 0.0);
    }

    #[test]
    fn test_calculate_accuracy_score_perfect() {
        // Identical images should give high accuracy
        let image: Vec<f32> = (0..TARGET_SIZE * TARGET_SIZE)
            .map(|i| if i % 10 == 0 { 0.0 } else { 1.0 })
            .collect();

        let score = calculate_accuracy_score(&image, &image);

        // Should be very high (close to 1.0)
        assert!(score > 0.9);
    }

    #[test]
    fn test_calculate_accuracy_score_empty_drawn() {
        let drawn: Vec<f32> = vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize]; // all white
        let reference: Vec<f32> = (0..TARGET_SIZE * TARGET_SIZE)
            .map(|i| if i % 10 == 0 { 0.0 } else { 1.0 })
            .collect();

        let score = calculate_accuracy_score(&drawn, &reference);

        // Should be 0 (nothing drawn)
        assert_eq!(score, 0.0);
    }

    #[test]
    fn test_calculate_stroke_similarity_identical() {
        // Identical images should give high similarity
        let image: Vec<f32> = (0..TARGET_SIZE * TARGET_SIZE)
            .map(|i| if i % 10 == 0 { 0.0 } else { 1.0 })
            .collect();

        let score = calculate_stroke_similarity(&image, &image);

        // Should be high (close to 1.0)
        assert!(score > 0.8);
    }

    #[test]
    fn test_calculate_stroke_similarity_empty() {
        let drawn: Vec<f32> = vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize]; // all white
        let reference: Vec<f32> = vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize];

        let score = calculate_stroke_similarity(&drawn, &reference);

        // Should be 0 (no content to compare)
        assert_eq!(score, 0.0);
    }

    #[test]
    fn test_encode_grayscale_to_png() {
        let img = GrayImage::from_pixel(10, 10, Luma([128u8]));
        let result = encode_grayscale_to_png(&img);

        assert!(result.is_ok());
        let png_bytes = result.unwrap();

        // PNG header signature
        assert!(png_bytes.len() > 8);
        assert_eq!(&png_bytes[0..8], &[137, 80, 78, 71, 13, 10, 26, 10]);
    }
}
