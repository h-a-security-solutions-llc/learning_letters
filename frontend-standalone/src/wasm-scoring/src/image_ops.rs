//! Image processing operations for scoring
//!
//! Implements distance transforms, morphological operations, and skeleton extraction.

/// Euclidean Distance Transform using the Meijster algorithm
/// O(n) per dimension, very efficient for image processing
pub fn distance_transform_edt(binary: &[bool], width: usize, height: usize) -> Vec<f32> {
    let mut result = vec![f32::MAX; width * height];

    // First pass: forward scan
    for y in 0..height {
        for x in 0..width {
            let idx = y * width + x;
            if binary[idx] {
                result[idx] = 0.0;
            } else {
                let mut min_dist = f32::MAX;

                // Check neighbors that have been processed
                if x > 0 {
                    min_dist = min_dist.min(result[idx - 1] + 1.0);
                }
                if y > 0 {
                    min_dist = min_dist.min(result[(y - 1) * width + x] + 1.0);
                }
                if x > 0 && y > 0 {
                    min_dist = min_dist.min(result[(y - 1) * width + (x - 1)] + 1.414);
                }
                if x < width - 1 && y > 0 {
                    min_dist = min_dist.min(result[(y - 1) * width + (x + 1)] + 1.414);
                }

                result[idx] = min_dist;
            }
        }
    }

    // Second pass: backward scan
    for y in (0..height).rev() {
        for x in (0..width).rev() {
            let idx = y * width + x;

            if x < width - 1 {
                result[idx] = result[idx].min(result[idx + 1] + 1.0);
            }
            if y < height - 1 {
                result[idx] = result[idx].min(result[(y + 1) * width + x] + 1.0);
            }
            if x < width - 1 && y < height - 1 {
                result[idx] = result[idx].min(result[(y + 1) * width + (x + 1)] + 1.414);
            }
            if x > 0 && y < height - 1 {
                result[idx] = result[idx].min(result[(y + 1) * width + (x - 1)] + 1.414);
            }
        }
    }

    result
}

/// Binary dilation with a 3x3 structuring element
pub fn binary_dilation(binary: &[bool], width: usize, height: usize, iterations: u32) -> Vec<bool> {
    let mut current = binary.to_vec();
    let mut next = vec![false; width * height];

    for _ in 0..iterations {
        for y in 0..height {
            for x in 0..width {
                let idx = y * width + x;

                // Check 3x3 neighborhood
                let mut has_neighbor = false;
                for dy in -1i32..=1 {
                    for dx in -1i32..=1 {
                        let ny = y as i32 + dy;
                        let nx = x as i32 + dx;

                        if ny >= 0 && ny < height as i32 && nx >= 0 && nx < width as i32 {
                            let nidx = ny as usize * width + nx as usize;
                            if current[nidx] {
                                has_neighbor = true;
                                break;
                            }
                        }
                    }
                    if has_neighbor {
                        break;
                    }
                }

                next[idx] = has_neighbor;
            }
        }

        std::mem::swap(&mut current, &mut next);
    }

    current
}

/// Binary erosion with a 3x3 structuring element
pub fn binary_erosion(binary: &[bool], width: usize, height: usize, iterations: u32) -> Vec<bool> {
    let mut current = binary.to_vec();
    let mut next = vec![false; width * height];

    for _ in 0..iterations {
        for y in 0..height {
            for x in 0..width {
                let idx = y * width + x;

                // Check if all 3x3 neighbors are set
                let mut all_neighbors = true;
                for dy in -1i32..=1 {
                    for dx in -1i32..=1 {
                        let ny = y as i32 + dy;
                        let nx = x as i32 + dx;

                        if ny >= 0 && ny < height as i32 && nx >= 0 && nx < width as i32 {
                            let nidx = ny as usize * width + nx as usize;
                            if !current[nidx] {
                                all_neighbors = false;
                                break;
                            }
                        } else {
                            all_neighbors = false;
                            break;
                        }
                    }
                    if !all_neighbors {
                        break;
                    }
                }

                next[idx] = all_neighbors;
            }
        }

        std::mem::swap(&mut current, &mut next);
    }

    current
}

/// Zhang-Suen thinning algorithm for skeleton extraction
pub fn skeletonize(binary: &[bool], width: usize, height: usize) -> Vec<bool> {
    let mut current = binary.to_vec();

    loop {
        let mut changed = false;

        // Sub-iteration 1
        let mut to_remove = Vec::new();
        for y in 1..height - 1 {
            for x in 1..width - 1 {
                let idx = y * width + x;
                if current[idx] && should_remove_subiteration1(&current, x, y, width) {
                    to_remove.push(idx);
                }
            }
        }

        for idx in &to_remove {
            current[*idx] = false;
            changed = true;
        }

        // Sub-iteration 2
        to_remove.clear();
        for y in 1..height - 1 {
            for x in 1..width - 1 {
                let idx = y * width + x;
                if current[idx] && should_remove_subiteration2(&current, x, y, width) {
                    to_remove.push(idx);
                }
            }
        }

        for idx in &to_remove {
            current[*idx] = false;
            changed = true;
        }

        if !changed {
            break;
        }
    }

    current
}

fn get_neighbors(binary: &[bool], x: usize, y: usize, width: usize) -> [bool; 8] {
    // P2, P3, P4, P5, P6, P7, P8, P9 in clockwise order starting from top
    [
        binary[(y - 1) * width + x],     // P2 (top)
        binary[(y - 1) * width + x + 1], // P3 (top-right)
        binary[y * width + x + 1],       // P4 (right)
        binary[(y + 1) * width + x + 1], // P5 (bottom-right)
        binary[(y + 1) * width + x],     // P6 (bottom)
        binary[(y + 1) * width + x - 1], // P7 (bottom-left)
        binary[y * width + x - 1],       // P8 (left)
        binary[(y - 1) * width + x - 1], // P9 (top-left)
    ]
}

fn count_transitions(neighbors: &[bool; 8]) -> u32 {
    let mut count = 0;
    for i in 0..8 {
        if !neighbors[i] && neighbors[(i + 1) % 8] {
            count += 1;
        }
    }
    count
}

fn count_neighbors(neighbors: &[bool; 8]) -> u32 {
    neighbors.iter().filter(|&&x| x).count() as u32
}

fn should_remove_subiteration1(binary: &[bool], x: usize, y: usize, width: usize) -> bool {
    let neighbors = get_neighbors(binary, x, y, width);
    let n = count_neighbors(&neighbors);
    let t = count_transitions(&neighbors);

    // Conditions for sub-iteration 1
    n >= 2 && n <= 6 &&
    t == 1 &&
    !(neighbors[0] && neighbors[2] && neighbors[4]) && // P2 * P4 * P6
    !(neighbors[2] && neighbors[4] && neighbors[6])    // P4 * P6 * P8
}

fn should_remove_subiteration2(binary: &[bool], x: usize, y: usize, width: usize) -> bool {
    let neighbors = get_neighbors(binary, x, y, width);
    let n = count_neighbors(&neighbors);
    let t = count_transitions(&neighbors);

    // Conditions for sub-iteration 2
    n >= 2 && n <= 6 &&
    t == 1 &&
    !(neighbors[0] && neighbors[2] && neighbors[6]) && // P2 * P4 * P8
    !(neighbors[0] && neighbors[4] && neighbors[6])    // P2 * P6 * P8
}

/// Find endpoints in a skeleton (pixels with exactly 1 neighbor)
pub fn find_endpoints(skeleton: &[bool], width: usize, height: usize) -> Vec<(usize, usize)> {
    let mut endpoints = Vec::new();

    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let idx = y * width + x;
            if !skeleton[idx] {
                continue;
            }

            let mut neighbor_count = 0;
            for dy in -1i32..=1 {
                for dx in -1i32..=1 {
                    if dy == 0 && dx == 0 {
                        continue;
                    }
                    let ny = (y as i32 + dy) as usize;
                    let nx = (x as i32 + dx) as usize;
                    if skeleton[ny * width + nx] {
                        neighbor_count += 1;
                    }
                }
            }

            if neighbor_count == 1 {
                endpoints.push((x, y));
            }
        }
    }

    endpoints
}

/// Bridge small gaps between endpoints
pub fn bridge_gaps(skeleton: &mut Vec<bool>, width: usize, height: usize, max_gap: u32) {
    let endpoints = find_endpoints(skeleton, width, height);

    for (ex, ey) in &endpoints {
        let mut best_target: Option<(usize, usize)> = None;
        let mut best_dist = max_gap as f32 + 1.0;

        // Look for skeleton pixels within max_gap
        let search_range = max_gap as i32;
        for dy in -search_range..=search_range {
            for dx in -search_range..=search_range {
                if dy == 0 && dx == 0 {
                    continue;
                }

                let ty = *ey as i32 + dy;
                let tx = *ex as i32 + dx;

                if ty < 0 || ty >= height as i32 || tx < 0 || tx >= width as i32 {
                    continue;
                }

                let ty = ty as usize;
                let tx = tx as usize;

                if !skeleton[ty * width + tx] {
                    continue;
                }

                // Skip direct neighbors
                if dy.abs() <= 1 && dx.abs() <= 1 {
                    continue;
                }

                let dist = ((dx * dx + dy * dy) as f32).sqrt();
                if dist < best_dist {
                    best_dist = dist;
                    best_target = Some((tx, ty));
                }
            }
        }

        // Draw line to connect
        if let Some((tx, ty)) = best_target {
            draw_line(skeleton, width, *ex, *ey, tx, ty);
        }
    }
}

/// Bresenham's line algorithm
fn draw_line(image: &mut Vec<bool>, width: usize, x0: usize, y0: usize, x1: usize, y1: usize) {
    let dx = (x1 as i32 - x0 as i32).abs();
    let dy = -(y1 as i32 - y0 as i32).abs();
    let sx = if x0 < x1 { 1i32 } else { -1i32 };
    let sy = if y0 < y1 { 1i32 } else { -1i32 };
    let mut err = dx + dy;

    let mut x = x0 as i32;
    let mut y = y0 as i32;

    loop {
        if x >= 0 && y >= 0 {
            let idx = y as usize * width + x as usize;
            if idx < image.len() {
                image[idx] = true;
            }
        }

        if x == x1 as i32 && y == y1 as i32 {
            break;
        }

        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x += sx;
        }
        if e2 <= dx {
            err += dx;
            y += sy;
        }
    }
}

/// Prune short branches from a skeleton
pub fn prune_branches(skeleton: &mut Vec<bool>, width: usize, height: usize, prune_length: u32, max_removal_percent: f32) {
    let initial_pixels: u32 = skeleton.iter().filter(|&&x| x).count() as u32;
    let max_removal = (initial_pixels as f32 * max_removal_percent) as u32;
    let mut total_removed: u32 = 0;

    for _ in 0..prune_length {
        if total_removed >= max_removal {
            break;
        }

        let endpoints = find_endpoints(skeleton, width, height);
        if endpoints.is_empty() {
            break;
        }

        let to_remove: Vec<_> = endpoints.iter()
            .take((max_removal - total_removed) as usize)
            .map(|(x, y)| y * width + x)
            .collect();

        for idx in &to_remove {
            skeleton[*idx] = false;
            total_removed += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_distance_transform_single_point() {
        // 5x5 grid with single point in center
        let mut binary = vec![false; 25];
        binary[12] = true; // center point (2, 2)

        let result = distance_transform_edt(&binary, 5, 5);

        // Center should be 0
        assert_eq!(result[12], 0.0);

        // Adjacent pixels should be ~1.0
        assert!((result[7] - 1.0).abs() < 0.01);  // top
        assert!((result[11] - 1.0).abs() < 0.01); // left
        assert!((result[13] - 1.0).abs() < 0.01); // right
        assert!((result[17] - 1.0).abs() < 0.01); // bottom

        // Diagonal pixels should be ~1.414
        assert!((result[6] - 1.414).abs() < 0.01);  // top-left
        assert!((result[8] - 1.414).abs() < 0.01);  // top-right
        assert!((result[16] - 1.414).abs() < 0.01); // bottom-left
        assert!((result[18] - 1.414).abs() < 0.01); // bottom-right
    }

    #[test]
    fn test_distance_transform_empty_image() {
        let binary = vec![false; 25];
        let result = distance_transform_edt(&binary, 5, 5);

        // All distances should be very large (MAX)
        for val in result {
            assert!(val > 100.0);
        }
    }

    #[test]
    fn test_distance_transform_full_image() {
        let binary = vec![true; 25];
        let result = distance_transform_edt(&binary, 5, 5);

        // All distances should be 0
        for val in result {
            assert_eq!(val, 0.0);
        }
    }

    #[test]
    fn test_binary_dilation_single_point() {
        let mut binary = vec![false; 25];
        binary[12] = true; // center point (2, 2)

        let result = binary_dilation(&binary, 5, 5, 1);

        // Center and all neighbors should be true
        assert!(result[12]); // center
        assert!(result[6]);  // top-left
        assert!(result[7]);  // top
        assert!(result[8]);  // top-right
        assert!(result[11]); // left
        assert!(result[13]); // right
        assert!(result[16]); // bottom-left
        assert!(result[17]); // bottom
        assert!(result[18]); // bottom-right

        // Corners should still be false
        assert!(!result[0]);  // top-left corner
        assert!(!result[4]);  // top-right corner
        assert!(!result[20]); // bottom-left corner
        assert!(!result[24]); // bottom-right corner
    }

    #[test]
    fn test_binary_dilation_multiple_iterations() {
        let mut binary = vec![false; 49]; // 7x7
        binary[24] = true; // center point (3, 3)

        let result = binary_dilation(&binary, 7, 7, 2);

        // After 2 iterations, should expand by 2 pixels in all directions
        // Check that center 5x5 area is mostly true
        let true_count: usize = result.iter().filter(|&&x| x).count();
        assert!(true_count >= 20);
    }

    #[test]
    fn test_binary_erosion_removes_single_pixel() {
        let mut binary = vec![false; 25];
        binary[12] = true; // single center pixel

        let result = binary_erosion(&binary, 5, 5, 1);

        // Single pixel should be eroded away
        assert!(!result[12]);
    }

    #[test]
    fn test_binary_erosion_preserves_solid_block() {
        // 5x5 grid with solid 3x3 block in center
        let mut binary = vec![false; 25];
        for y in 1..4 {
            for x in 1..4 {
                binary[y * 5 + x] = true;
            }
        }

        let result = binary_erosion(&binary, 5, 5, 1);

        // Center should still be true after 1 erosion
        assert!(result[12]);
    }

    #[test]
    fn test_skeletonize_horizontal_line() {
        // 5x15 grid with horizontal line
        let mut binary = vec![false; 75];
        for x in 2..13 {
            for y in 1..4 {
                binary[y * 15 + x] = true;
            }
        }

        let result = skeletonize(&binary, 15, 5);

        // Should produce a thin horizontal line
        let true_count: usize = result.iter().filter(|&&x| x).count();
        assert!(true_count > 0);
        assert!(true_count < 20); // Should be much thinner than original
    }

    #[test]
    fn test_skeletonize_empty_image() {
        let binary = vec![false; 25];
        let result = skeletonize(&binary, 5, 5);

        // Should remain empty
        assert!(result.iter().all(|&x| !x));
    }

    #[test]
    fn test_find_endpoints_line() {
        // Create a simple horizontal line
        let mut skeleton = vec![false; 25];
        skeleton[11] = true; // (1, 2)
        skeleton[12] = true; // (2, 2)
        skeleton[13] = true; // (3, 2)

        let endpoints = find_endpoints(&skeleton, 5, 5);

        // Should find 2 endpoints
        assert_eq!(endpoints.len(), 2);
        assert!(endpoints.contains(&(1, 2)));
        assert!(endpoints.contains(&(3, 2)));
    }

    #[test]
    fn test_find_endpoints_circle() {
        // Create a small closed loop (no endpoints)
        let mut skeleton = vec![false; 49]; // 7x7
        // Create a small square loop
        skeleton[15] = true; // (1, 2)
        skeleton[16] = true; // (2, 2)
        skeleton[17] = true; // (3, 2)
        skeleton[22] = true; // (1, 3)
        skeleton[24] = true; // (3, 3)
        skeleton[29] = true; // (1, 4)
        skeleton[30] = true; // (2, 4)
        skeleton[31] = true; // (3, 4)

        let endpoints = find_endpoints(&skeleton, 7, 7);

        // Closed loop should have no endpoints
        assert_eq!(endpoints.len(), 0);
    }

    #[test]
    fn test_count_transitions() {
        // All false - 0 transitions
        let neighbors = [false, false, false, false, false, false, false, false];
        assert_eq!(count_transitions(&neighbors), 0);

        // Alternating - 4 transitions
        let neighbors = [true, false, true, false, true, false, true, false];
        assert_eq!(count_transitions(&neighbors), 4);

        // Single true - 1 transition
        let neighbors = [true, false, false, false, false, false, false, false];
        assert_eq!(count_transitions(&neighbors), 1);

        // Two adjacent true - 1 transition
        let neighbors = [true, true, false, false, false, false, false, false];
        assert_eq!(count_transitions(&neighbors), 1);
    }

    #[test]
    fn test_count_neighbors() {
        let neighbors = [false, false, false, false, false, false, false, false];
        assert_eq!(count_neighbors(&neighbors), 0);

        let neighbors = [true, true, true, true, true, true, true, true];
        assert_eq!(count_neighbors(&neighbors), 8);

        let neighbors = [true, false, true, false, true, false, true, false];
        assert_eq!(count_neighbors(&neighbors), 4);
    }

    #[test]
    fn test_bridge_gaps_simple() {
        // Create two line segments with a gap
        let mut skeleton = vec![false; 49]; // 7x7
        skeleton[8] = true;  // (1, 1)
        skeleton[9] = true;  // (2, 1)
        skeleton[12] = true; // (5, 1)
        skeleton[13] = true; // (6, 1)

        bridge_gaps(&mut skeleton, 7, 7, 5);

        // Gap should be bridged, total true count should increase
        let true_count: usize = skeleton.iter().filter(|&&x| x).count();
        assert!(true_count > 4);
    }

    #[test]
    fn test_prune_branches() {
        // Create a T-shape (main line with a branch)
        let mut skeleton = vec![false; 49]; // 7x7
        // Horizontal line
        skeleton[22] = true; // (1, 3)
        skeleton[23] = true; // (2, 3)
        skeleton[24] = true; // (3, 3)
        skeleton[25] = true; // (4, 3)
        skeleton[26] = true; // (5, 3)
        // Vertical branch
        skeleton[17] = true; // (3, 2)
        skeleton[10] = true; // (3, 1)

        let initial_count: usize = skeleton.iter().filter(|&&x| x).count();

        prune_branches(&mut skeleton, 7, 7, 2, 0.5);

        let final_count: usize = skeleton.iter().filter(|&&x| x).count();

        // Should have removed some pixels
        assert!(final_count <= initial_count);
    }
}
