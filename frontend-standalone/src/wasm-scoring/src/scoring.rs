//! Main scoring logic for character recognition
//!
//! Implements the scoring algorithm that compares user drawings against reference images.

use crate::image_ops::binary_dilation;
use crate::WasmScoringResult;
use crate::ScoringResult;
use image::{GrayImage, ImageBuffer, Luma, ImageEncoder};
use image::codecs::png::PngEncoder;
use rusttype::{Font, Scale, point};
use web_sys::console;

const TARGET_SIZE: u32 = 200;  // Increased from 128 for better detail
const THRESHOLD: u8 = 200;
// Binary thresholds: lower = stricter (only very dark pixels count as strokes)
// User drawings have solid black strokes (~0.0-0.3)
// Reference has anti-aliased edges (~0.0-0.95)
const USER_BINARY_THRESHOLD: f32 = 0.85;   // Lenient for user - captures all strokes
const REF_BINARY_THRESHOLD: f32 = 0.70;    // Stricter for reference - avoid anti-alias halo

// Helper macro for console logging - only logs in WASM target
#[cfg(target_arch = "wasm32")]
macro_rules! log {
    ($($t:tt)*) => {
        console::log_1(&format!($($t)*).into());
    }
}

#[cfg(not(target_arch = "wasm32"))]
macro_rules! log {
    ($($t:tt)*) => {
        // No-op in native tests
    }
}

/// Main scoring function
pub fn score_drawing_internal(
    image_data: &[u8],
    character: char,
    font_data: &[u8],
) -> Result<WasmScoringResult, String> {
    log!("[WASM] === SCORING START ===");
    log!("[WASM] Character: '{}', Image: {} bytes", character, image_data.len());

    // Decode the user's drawing
    let drawn_image = image::load_from_memory(image_data)
        .map_err(|e| format!("Failed to decode image: {}", e))?;

    let (img_width, img_height) = (drawn_image.width(), drawn_image.height());
    log!("[WASM] User image decoded: {}x{}", img_width, img_height);

    // Convert to RGBA and composite against white background
    // This handles transparent canvases correctly (transparent -> white, not black)
    let rgba = drawn_image.to_rgba8();
    let mut composited: GrayImage = ImageBuffer::new(img_width, img_height);
    for y in 0..img_height {
        for x in 0..img_width {
            let pixel = rgba.get_pixel(x, y);
            let r = pixel[0] as f32;
            let g = pixel[1] as f32;
            let b = pixel[2] as f32;
            let a = pixel[3] as f32 / 255.0;  // Alpha as 0.0-1.0

            // Composite against white (255) background
            // result = foreground * alpha + background * (1 - alpha)
            let gray = 0.299 * r + 0.587 * g + 0.114 * b;  // Standard luminance
            let composited_value = gray * a + 255.0 * (1.0 - a);

            composited.put_pixel(x, y, Luma([composited_value as u8]));
        }
    }
    log!("[WASM] Composited against white background");

    // Generate reference image at same size as TARGET_SIZE
    let reference_image = generate_reference_gray(character, font_data, TARGET_SIZE)?;

    // Process both images
    let drawn_processed = extract_and_center_character(&composited);
    let reference_processed = extract_and_center_character(&reference_image);

    // Count pixels at different thresholds to debug
    let drawn_dark_50 = drawn_processed.iter().filter(|&&v| v < 0.5).count();
    let drawn_dark_85 = drawn_processed.iter().filter(|&&v| v < 0.85).count();
    let ref_dark_50 = reference_processed.iter().filter(|&&v| v < 0.5).count();

    log!("[WASM] User drawing pixels: {} (threshold 0.5), {} (threshold 0.85)", drawn_dark_50, drawn_dark_85);
    log!("[WASM] Reference pixels: {} (threshold 0.5)", ref_dark_50);

    // Calculate scores
    log!("[WASM] Calculating coverage score...");
    let coverage = calculate_coverage_score(&drawn_processed, &reference_processed);
    log!("[WASM] Coverage: {:.1}%", coverage * 100.0);

    log!("[WASM] Calculating accuracy score...");
    let accuracy = calculate_accuracy_score(&drawn_processed, &reference_processed);
    log!("[WASM] Accuracy: {:.1}%", accuracy * 100.0);

    log!("[WASM] Calculating similarity score...");
    let similarity = calculate_stroke_similarity(&drawn_processed, &reference_processed);
    log!("[WASM] Similarity: {:.1}%", similarity * 100.0);

    // Combined score with weights: 40% coverage, 30% accuracy, 30% similarity
    // Prioritize coverage for kindergarteners - they need to trace the whole letter
    let combined_score = coverage * 0.40 + accuracy * 0.30 + similarity * 0.30;
    let percentage_score = (combined_score * 100.0).min(100.0).max(0.0) as u8;
    log!("[WASM] Combined score: {}% (coverage*0.40 + accuracy*0.30 + similarity*0.30)", percentage_score);

    // Star rating
    let (stars, feedback) = get_star_rating(percentage_score);
    log!("[WASM] Rating: {} stars - {}", stars, feedback);

    // Generate reference image PNG for display
    let reference_png = encode_grayscale_to_png(&reference_image)?;

    // Generate debug images showing what was actually compared
    let debug_user_png = encode_processed_to_png(&drawn_processed, TARGET_SIZE)?;
    let debug_ref_png = encode_processed_to_png(&reference_processed, TARGET_SIZE)?;

    log!("[WASM] === SCORING COMPLETE ===");

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
        debug_user_processed: debug_user_png,
        debug_reference_processed: debug_ref_png,
    })
}

/// Generate a reference image as PNG bytes
pub fn generate_reference_image_internal(
    character: char,
    font_data: &[u8],
    size: u32,
) -> Result<Vec<u8>, String> {
    log!("[WASM] Generating reference image for '{}' at {}x{}", character, size, size);
    let gray = generate_reference_gray(character, font_data, size)?;
    encode_grayscale_to_png(&gray)
}

fn generate_reference_gray(character: char, font_data: &[u8], size: u32) -> Result<GrayImage, String> {
    let font = Font::try_from_bytes(font_data)
        .ok_or("Failed to parse font data")?;

    let mut img: GrayImage = ImageBuffer::from_pixel(size, size, Luma([255u8]));

    let font_size = size as f32 * 0.75;
    let scale = Scale::uniform(font_size);

    // Get glyph metrics for centering - position at origin first to get bounding box
    let glyph = font.glyph(character).scaled(scale).positioned(point(0.0, 0.0));

    if let Some(bb) = glyph.pixel_bounding_box() {
        let glyph_width = bb.max.x - bb.min.x;
        let glyph_height = bb.max.y - bb.min.y;

        // Calculate offset to truly center the glyph in the image
        // We need to offset so the glyph's bounding box is centered
        let x_offset = ((size as i32 - glyph_width) / 2) - bb.min.x;
        let y_offset = ((size as i32 - glyph_height) / 2) - bb.min.y;

        // Reposition glyph with centering offsets (no additional baseline offset)
        let glyph = font.glyph(character)
            .scaled(scale)
            .positioned(point(x_offset as f32, y_offset as f32));

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

/// Convert processed image (Vec<f32>) back to PNG for debugging
fn encode_processed_to_png(processed: &[f32], size: u32) -> Result<Vec<u8>, String> {
    let mut img: GrayImage = ImageBuffer::new(size, size);

    for y in 0..size {
        for x in 0..size {
            let idx = (y * size + x) as usize;
            let value = if idx < processed.len() {
                (processed[idx] * 255.0) as u8
            } else {
                255
            };
            img.put_pixel(x, y, Luma([value]));
        }
    }

    encode_grayscale_to_png(&img)
}

/// Extract the drawn character, center it, and normalize to target size
/// Uses simple bilinear interpolation for clean, predictable output
fn extract_and_center_character(image: &GrayImage) -> Vec<f32> {
    let (width, height) = image.dimensions();

    // First, detect background color by sampling corners
    let corners = [
        image.get_pixel(0, 0).0[0],
        image.get_pixel(width - 1, 0).0[0],
        image.get_pixel(0, height - 1).0[0],
        image.get_pixel(width - 1, height - 1).0[0],
    ];
    let background = corners.iter().copied().max().unwrap_or(255);

    log!("[WASM Extract] Input image: {}x{}, detected background: {}", width, height, background);

    // Threshold for detecting strokes - must be significantly darker than background
    // If background is 255 (white), threshold ~180 catches dark strokes
    // If background is darker (e.g., 200), adjust threshold accordingly
    let threshold = if background > 200 {
        // Normal white/light background - use fixed threshold
        180u8
    } else {
        // Darker background - strokes must be much darker than background
        (background as f32 * 0.5) as u8
    };

    // Find bounding box of drawn content
    let mut min_x = width;
    let mut max_x = 0;
    let mut min_y = height;
    let mut max_y = 0;
    let mut drawn_count = 0u32;

    for y in 0..height {
        for x in 0..width {
            let pixel = image.get_pixel(x, y).0[0];
            if pixel < threshold {
                drawn_count += 1;
                min_x = min_x.min(x);
                max_x = max_x.max(x);
                min_y = min_y.min(y);
                max_y = max_y.max(y);
            }
        }
    }

    log!("[WASM Extract] Found {} dark pixels (threshold={})", drawn_count, threshold);

    if drawn_count == 0 {
        log!("[WASM Extract] No content found, returning white image");
        return vec![1.0; (TARGET_SIZE * TARGET_SIZE) as usize];
    }

    // Add padding around the bounding box
    let padding = 5u32;
    let min_x = min_x.saturating_sub(padding);
    let max_x = (max_x + padding).min(width - 1);
    let min_y = min_y.saturating_sub(padding);
    let max_y = (max_y + padding).min(height - 1);

    let region_width = max_x - min_x + 1;
    let region_height = max_y - min_y + 1;

    log!("[WASM Extract] Bounding box: ({},{}) to ({},{}) = {}x{}",
         min_x, min_y, max_x, max_y, region_width, region_height);

    // Scale to fit with margin (10% margin on each side)
    let margin = TARGET_SIZE as f32 * 0.1;
    let available = TARGET_SIZE as f32 - 2.0 * margin;
    let scale = (available / region_width as f32).min(available / region_height as f32);

    let new_width = (region_width as f32 * scale) as u32;
    let new_height = (region_height as f32 * scale) as u32;

    let x_offset = (TARGET_SIZE - new_width) / 2;
    let y_offset = (TARGET_SIZE - new_height) / 2;

    log!("[WASM Extract] Scale factor: {:.3}, new size: {}x{}", scale, new_width, new_height);

    let mut output = vec![1.0f32; (TARGET_SIZE * TARGET_SIZE) as usize];

    // Simple bilinear interpolation - preserves grayscale correctly
    for ty in 0..new_height {
        for tx in 0..new_width {
            let src_x = min_x as f32 + (tx as f32 / scale);
            let src_y = min_y as f32 + (ty as f32 / scale);

            let x0 = src_x.floor() as u32;
            let y0 = src_y.floor() as u32;
            let x1 = (x0 + 1).min(width - 1);
            let y1 = (y0 + 1).min(height - 1);

            let fx = src_x - x0 as f32;
            let fy = src_y - y0 as f32;

            let p00 = image.get_pixel(x0, y0).0[0] as f32;
            let p10 = image.get_pixel(x1, y0).0[0] as f32;
            let p01 = image.get_pixel(x0, y1).0[0] as f32;
            let p11 = image.get_pixel(x1, y1).0[0] as f32;

            let value = p00 * (1.0 - fx) * (1.0 - fy)
                      + p10 * fx * (1.0 - fy)
                      + p01 * (1.0 - fx) * fy
                      + p11 * fx * fy;

            let dst_idx = ((y_offset + ty) * TARGET_SIZE + (x_offset + tx)) as usize;
            output[dst_idx] = value / 255.0;
        }
    }

    let output_dark_count = output.iter().filter(|&&v| v < 0.9).count();
    log!("[WASM Extract] Output has {} dark pixels in {}x{} image",
         output_dark_count, TARGET_SIZE, TARGET_SIZE);

    output
}

/// Simple approach: just dilate the binary image to normalize thickness
/// No skeletonization - it was destroying thin strokes
fn normalize_with_dilation(binary: &[bool], width: usize, height: usize, iterations: u32) -> Vec<bool> {
    if !binary.iter().any(|&x| x) {
        return binary.to_vec();
    }
    binary_dilation(binary, width, height, iterations)
}

/// Calculate coverage score: how much of the reference is covered by the user's drawing
fn calculate_coverage_score(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;

    // Convert to binary with appropriate thresholds
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < USER_BINARY_THRESHOLD).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < REF_BINARY_THRESHOLD).collect();

    let drawn_count = drawn_binary.iter().filter(|&&x| x).count();
    let ref_count = reference_binary.iter().filter(|&&x| x).count();

    log!("[Coverage] User strokes: {}, Reference strokes: {}", drawn_count, ref_count);

    if drawn_count == 0 || ref_count == 0 {
        return 0.0;
    }

    // Dilate user's drawing to allow positional errors from hand-drawing
    // 7 iterations on 200px = ~3.5% radius tolerance
    let drawn_dilated = normalize_with_dilation(&drawn_binary, size, size, 7);

    // Count how many reference pixels overlap with dilated user drawing
    let covered: u32 = reference_binary.iter()
        .zip(drawn_dilated.iter())
        .filter(|(&is_ref, &is_drawn)| is_ref && is_drawn)
        .count() as u32;

    log!("[Coverage] Covered {} of {} reference pixels", covered, ref_count);

    (covered as f32 / ref_count as f32).min(1.0)
}

/// Calculate accuracy score: how much of the user's drawing is on/near the reference
fn calculate_accuracy_score(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;

    // Convert to binary with appropriate thresholds
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < USER_BINARY_THRESHOLD).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < REF_BINARY_THRESHOLD).collect();

    let drawn_count = drawn_binary.iter().filter(|&&x| x).count();
    let ref_count = reference_binary.iter().filter(|&&x| x).count();

    if drawn_count == 0 || ref_count == 0 {
        return 0.0;
    }

    // Create acceptable zone by dilating the reference
    // 7 iterations = ~3.5% radius tolerance
    let reference_zone = normalize_with_dilation(&reference_binary, size, size, 7);

    // Count user's drawn pixels that fall within the acceptable zone
    let within_bounds: u32 = drawn_binary.iter()
        .zip(reference_zone.iter())
        .filter(|(&is_drawn, &is_zone)| is_drawn && is_zone)
        .count() as u32;

    log!("[Accuracy] {} of {} user pixels within reference zone", within_bounds, drawn_count);

    (within_bounds as f32 / drawn_count as f32).min(1.0)
}

/// Calculate stroke similarity using IoU with modest dilation
fn calculate_stroke_similarity(drawn: &[f32], reference: &[f32]) -> f32 {
    let size = TARGET_SIZE as usize;

    // Convert to binary with appropriate thresholds
    let drawn_binary: Vec<bool> = drawn.iter().map(|&v| v < USER_BINARY_THRESHOLD).collect();
    let reference_binary: Vec<bool> = reference.iter().map(|&v| v < REF_BINARY_THRESHOLD).collect();

    let drawn_count = drawn_binary.iter().filter(|&&x| x).count();
    let ref_count = reference_binary.iter().filter(|&&x| x).count();

    if drawn_count == 0 || ref_count == 0 {
        return 0.0;
    }

    // Dilate both images before IoU comparison
    // 14 iterations = ~7% radius tolerance - forgiving for hand-drawn shapes
    let drawn_dilated = normalize_with_dilation(&drawn_binary, size, size, 14);
    let ref_dilated = normalize_with_dilation(&reference_binary, size, size, 14);

    let intersection: u32 = drawn_dilated.iter()
        .zip(ref_dilated.iter())
        .filter(|(&d, &r)| d && r)
        .count() as u32;
    let union: u32 = drawn_dilated.iter()
        .zip(ref_dilated.iter())
        .filter(|(&d, &r)| d || r)
        .count() as u32;

    log!("[Similarity] Intersection: {}, Union: {}, IoU: {:.3}",
         intersection, union, intersection as f32 / (union as f32 + 1e-8));

    // Natural IoU scoring - no artificial boost
    intersection as f32 / (union as f32 + 1e-8)
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
    fn test_normalize_with_dilation_empty() {
        let binary = vec![false; 100];
        let result = normalize_with_dilation(&binary, 10, 10, 2);

        // Should remain empty
        assert!(result.iter().all(|&x| !x));
    }

    #[test]
    fn test_normalize_with_dilation_with_content() {
        // Create a small square
        let mut binary = vec![false; 100];
        for y in 4..6 {
            for x in 4..6 {
                binary[y * 10 + x] = true;
            }
        }

        let original_count: usize = binary.iter().filter(|&&x| x).count();
        let result = normalize_with_dilation(&binary, 10, 10, 1);
        let result_count: usize = result.iter().filter(|&&x| x).count();

        // Dilation should expand the shape
        assert!(result_count > 0);
        assert!(result_count >= original_count);
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

#[cfg(test)]
mod integration_tests {
    use super::*;
    use std::f32::consts::PI;

    /// Helper to create a C-shaped drawing programmatically
    fn create_c_shape(size: u32, stroke_width: u32, quality: f32) -> GrayImage {
        let mut img: GrayImage = ImageBuffer::from_pixel(size, size, Luma([255u8]));

        let cx = size as f32 / 2.0;
        let cy = size as f32 / 2.0;
        let radius = size as f32 * 0.35;

        // Draw C shape - arc from ~45 degrees to ~315 degrees
        // quality affects how much of the arc is drawn (1.0 = full, 0.5 = half)
        let start_angle = 45.0 * PI / 180.0;
        let end_angle = 315.0 * PI / 180.0;
        let arc_length = (end_angle - start_angle) * quality;

        for i in 0..500 {
            let t = i as f32 / 500.0;
            let angle = start_angle + arc_length * t;
            let x = cx + radius * angle.cos();
            let y = cy + radius * angle.sin();

            // Draw stroke with given width
            for dx in 0..stroke_width {
                for dy in 0..stroke_width {
                    let px = (x as i32 + dx as i32 - stroke_width as i32 / 2) as u32;
                    let py = (y as i32 + dy as i32 - stroke_width as i32 / 2) as u32;
                    if px < size && py < size {
                        img.put_pixel(px, py, Luma([20u8]));
                    }
                }
            }
        }

        img
    }

    /// Helper to create a zig-zag scribble (bad drawing)
    fn create_zigzag(size: u32) -> GrayImage {
        let mut img: GrayImage = ImageBuffer::from_pixel(size, size, Luma([255u8]));

        // Draw random zig-zag that doesn't resemble a C
        let mut x = size / 4;
        let mut y = size / 4;
        let mut direction = 1i32;

        while y < size * 3 / 4 {
            // Draw stroke
            for dx in 0..8 {
                for dy in 0..8 {
                    let px = (x as i32 + dx) as u32;
                    let py = (y as i32 + dy) as u32;
                    if px < size && py < size {
                        img.put_pixel(px, py, Luma([30u8]));
                    }
                }
            }

            // Move in zig-zag pattern
            x = ((x as i32) + direction * 15).max(50).min(size as i32 - 50) as u32;
            y += 4;
            if x >= size - 60 || x <= 60 {
                direction = -direction;
            }
        }

        img
    }

    /// Helper to create an empty canvas
    fn create_empty(size: u32) -> GrayImage {
        ImageBuffer::from_pixel(size, size, Luma([255u8]))
    }

    /// Helper to load font data for tests
    fn load_test_font() -> Vec<u8> {
        // Try to load from fixtures first
        if let Ok(data) = std::fs::read("tests/fixtures/Fredoka-Regular.ttf") {
            return data;
        }
        // Fallback to public fonts directory
        std::fs::read("../public/fonts/Fredoka-Regular.ttf")
            .or_else(|_| std::fs::read("../../public/fonts/Fredoka-Regular.ttf"))
            .expect("Could not find Fredoka-Regular.ttf font file")
    }

    /// Encode GrayImage to PNG bytes for scoring
    fn image_to_png(img: &GrayImage) -> Vec<u8> {
        let mut buffer = Vec::new();
        let encoder = image::codecs::png::PngEncoder::new(&mut buffer);
        encoder.write_image(
            img.as_raw(),
            img.width(),
            img.height(),
            image::ExtendedColorType::L8,
        ).expect("Failed to encode PNG");
        buffer
    }

    #[test]
    fn test_good_drawing_scores_high() {
        let img = create_c_shape(400, 12, 1.0);
        let image_data = image_to_png(&img);
        let font_data = load_test_font();

        let result = score_drawing_internal(&image_data, 'C', &font_data)
            .expect("Scoring should succeed");

        println!("Good C drawing: score={}%, stars={}, coverage={}%, accuracy={}%, similarity={}%",
            result.inner.score, result.inner.stars,
            result.inner.coverage, result.inner.accuracy, result.inner.similarity);

        assert!(result.inner.score >= 60,
            "Good drawing should score 60%+, got {}%", result.inner.score);
        assert!(result.inner.stars >= 3,
            "Good drawing should get 3+ stars, got {}", result.inner.stars);
    }

    #[test]
    fn test_zigzag_scores_low() {
        let img = create_zigzag(400);
        let image_data = image_to_png(&img);
        let font_data = load_test_font();

        let result = score_drawing_internal(&image_data, 'C', &font_data)
            .expect("Scoring should succeed");

        println!("Zigzag drawing: score={}%, stars={}, coverage={}%, accuracy={}%, similarity={}%",
            result.inner.score, result.inner.stars,
            result.inner.coverage, result.inner.accuracy, result.inner.similarity);

        assert!(result.inner.score <= 50,
            "Zig-zag should score <=50%, got {}%", result.inner.score);
        assert!(result.inner.stars <= 3,
            "Zig-zag should get <=3 stars, got {}", result.inner.stars);
    }

    #[test]
    fn test_empty_canvas_scores_zero() {
        let img = create_empty(400);
        let image_data = image_to_png(&img);
        let font_data = load_test_font();

        let result = score_drawing_internal(&image_data, 'C', &font_data)
            .expect("Scoring should succeed");

        println!("Empty canvas: score={}%, stars={}", result.inner.score, result.inner.stars);

        assert_eq!(result.inner.score, 0,
            "Empty canvas should score 0%, got {}%", result.inner.score);
        assert_eq!(result.inner.stars, 1,
            "Empty canvas should get 1 star, got {}", result.inner.stars);
    }

    #[test]
    fn test_partial_drawing_scores_medium() {
        // Draw only half of the C
        let img = create_c_shape(400, 12, 0.5);
        let image_data = image_to_png(&img);
        let font_data = load_test_font();

        let result = score_drawing_internal(&image_data, 'C', &font_data)
            .expect("Scoring should succeed");

        println!("Partial C drawing: score={}%, stars={}, coverage={}%, accuracy={}%, similarity={}%",
            result.inner.score, result.inner.stars,
            result.inner.coverage, result.inner.accuracy, result.inner.similarity);

        // Partial drawing should score somewhere in the middle
        assert!(result.inner.score >= 20 && result.inner.score <= 70,
            "Partial drawing should score 20-70%, got {}%", result.inner.score);
    }

    #[test]
    fn test_score_differentiation() {
        let font_data = load_test_font();

        let good_img = create_c_shape(400, 12, 1.0);
        let good = score_drawing_internal(&image_to_png(&good_img), 'C', &font_data)
            .expect("Good scoring should succeed");

        let bad_img = create_zigzag(400);
        let bad = score_drawing_internal(&image_to_png(&bad_img), 'C', &font_data)
            .expect("Bad scoring should succeed");

        println!("Differentiation test: good={}%, bad={}%, diff={}",
            good.inner.score, bad.inner.score,
            good.inner.score as i32 - bad.inner.score as i32);

        assert!(good.inner.score > bad.inner.score + 15,
            "Good ({}) should score 15+ points higher than bad ({})",
            good.inner.score, bad.inner.score);
    }

    #[test]
    fn test_very_good_drawing_gets_high_stars() {
        // Create a well-formed C with good stroke width
        let img = create_c_shape(400, 15, 1.0);
        let image_data = image_to_png(&img);
        let font_data = load_test_font();

        let result = score_drawing_internal(&image_data, 'C', &font_data)
            .expect("Scoring should succeed");

        println!("Very good C: score={}%, stars={}, coverage={}%, accuracy={}%, similarity={}%",
            result.inner.score, result.inner.stars,
            result.inner.coverage, result.inner.accuracy, result.inner.similarity);

        // A well-formed C should be able to achieve high scores
        assert!(result.inner.score >= 50,
            "Well-formed C should score 50%+, got {}%", result.inner.score);
    }
}
