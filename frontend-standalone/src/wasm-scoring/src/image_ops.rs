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
