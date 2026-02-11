//! Stroke Extraction Module
//!
//! Extracts stroke paths from font glyphs for guided tracing.
//! Pipeline: Font TTF -> Render glyph -> Skeletonize -> Trace paths -> Order strokes -> Smooth

use serde::{Deserialize, Serialize};
use crate::image_ops::{skeletonize, find_endpoints, prune_branches, bridge_gaps};
use rusttype::{Font, Scale, point};
use image::{GrayImage, ImageBuffer, Luma};

/// A point in the skeleton with metadata
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SkeletonPoint {
    pub x: usize,
    pub y: usize,
    pub is_endpoint: bool,
    pub is_junction: bool,
}

/// A stroke zone (start or end region)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrokeZone {
    pub cx: f32,
    pub cy: f32,
    pub r: f32,
}

/// A single stroke with its path and zones
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Stroke {
    /// Points in 0-100 coordinate space (normalized)
    pub points: Vec<[f32; 2]>,
    /// Start zone for guided tracing
    pub start_zone: StrokeZone,
    /// End zone for guided tracing
    pub end_zone: StrokeZone,
    /// Direction hint for instruction text
    pub direction: String,
}

/// Complete stroke data for a character
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StrokeData {
    pub character: String,
    pub font: String,
    #[serde(rename = "type")]
    pub char_type: String,
    pub strokes: Vec<Stroke>,
}

/// Union-Find data structure for connected component labeling
struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<usize>,
}

impl UnionFind {
    fn new(size: usize) -> Self {
        UnionFind {
            parent: (0..size).collect(),
            rank: vec![0; size],
        }
    }

    fn find(&mut self, x: usize) -> usize {
        if self.parent[x] != x {
            self.parent[x] = self.find(self.parent[x]); // Path compression
        }
        self.parent[x]
    }

    fn union(&mut self, x: usize, y: usize) {
        let px = self.find(x);
        let py = self.find(y);
        if px == py {
            return;
        }
        // Union by rank
        if self.rank[px] < self.rank[py] {
            self.parent[px] = py;
        } else if self.rank[px] > self.rank[py] {
            self.parent[py] = px;
        } else {
            self.parent[py] = px;
            self.rank[px] += 1;
        }
    }
}

/// Connected component labeling using union-find
/// Returns a label array where each pixel has its component ID (0 = background)
pub fn connected_components(binary: &[bool], width: usize, height: usize) -> (Vec<usize>, usize) {
    let size = width * height;
    let mut labels = vec![0usize; size];
    let mut uf = UnionFind::new(size + 1); // +1 for 1-based labels
    let mut next_label = 1usize;

    // First pass: assign provisional labels
    for y in 0..height {
        for x in 0..width {
            let idx = y * width + x;
            if !binary[idx] {
                continue;
            }

            // Get labels of neighbors already processed (left, top, top-left, top-right)
            let mut neighbor_labels = Vec::new();

            if x > 0 && binary[idx - 1] {
                neighbor_labels.push(labels[idx - 1]);
            }
            if y > 0 {
                let top_idx = (y - 1) * width + x;
                if binary[top_idx] {
                    neighbor_labels.push(labels[top_idx]);
                }
                if x > 0 && binary[top_idx - 1] {
                    neighbor_labels.push(labels[top_idx - 1]);
                }
                if x < width - 1 && binary[top_idx + 1] {
                    neighbor_labels.push(labels[top_idx + 1]);
                }
            }

            if neighbor_labels.is_empty() {
                // New component
                labels[idx] = next_label;
                next_label += 1;
            } else {
                // Use minimum label and union with others
                let min_label = *neighbor_labels.iter().min().unwrap();
                labels[idx] = min_label;
                for &nl in &neighbor_labels {
                    if nl != min_label {
                        uf.union(min_label, nl);
                    }
                }
            }
        }
    }

    // Second pass: relabel with canonical labels
    let mut label_map = std::collections::HashMap::new();
    let mut final_label = 0usize;

    for idx in 0..size {
        if labels[idx] == 0 {
            continue;
        }
        let root = uf.find(labels[idx]);
        let new_label = *label_map.entry(root).or_insert_with(|| {
            final_label += 1;
            final_label
        });
        labels[idx] = new_label;
    }

    (labels, final_label)
}

/// Count neighbors in 8-connectivity
fn count_neighbors_at(binary: &[bool], x: usize, y: usize, width: usize, height: usize) -> usize {
    let mut count = 0;
    for dy in -1i32..=1 {
        for dx in -1i32..=1 {
            if dy == 0 && dx == 0 {
                continue;
            }
            let nx = x as i32 + dx;
            let ny = y as i32 + dy;
            if nx >= 0 && nx < width as i32 && ny >= 0 && ny < height as i32 {
                if binary[ny as usize * width + nx as usize] {
                    count += 1;
                }
            }
        }
    }
    count
}

/// Find junction points (pixels with 3+ neighbors)
pub fn find_junctions(skeleton: &[bool], width: usize, height: usize) -> Vec<(usize, usize)> {
    let mut junctions = Vec::new();
    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let idx = y * width + x;
            if !skeleton[idx] {
                continue;
            }
            let neighbor_count = count_neighbors_at(skeleton, x, y, width, height);
            if neighbor_count >= 3 {
                junctions.push((x, y));
            }
        }
    }
    junctions
}

/// Raw path as a sequence of coordinates
#[derive(Debug, Clone)]
pub struct RawPath {
    pub points: Vec<(usize, usize)>,
    pub is_closed: bool,
}

/// Calculate angle between two vectors in degrees
fn angle_between_vectors(v1: (f32, f32), v2: (f32, f32)) -> f32 {
    let dot = v1.0 * v2.0 + v1.1 * v2.1;
    let mag1 = (v1.0 * v1.0 + v1.1 * v1.1).sqrt();
    let mag2 = (v2.0 * v2.0 + v2.1 * v2.1).sqrt();

    if mag1 < 0.001 || mag2 < 0.001 {
        return 0.0;
    }

    let cos_angle = (dot / (mag1 * mag2)).clamp(-1.0, 1.0);
    cos_angle.acos().to_degrees()
}

/// Split a path at sharp corners (angle changes > threshold)
/// Returns multiple paths if corners are found
fn split_at_corners(path: &RawPath, angle_threshold: f32, min_segment_length: usize) -> Vec<RawPath> {
    if path.points.len() < 5 {
        return vec![path.clone()];
    }

    let points = &path.points;
    let mut corner_indices = Vec::new();

    // Use a sliding window to detect angle changes
    // We need enough points on each side to calculate a reliable direction
    let window_size = 3;

    for i in window_size..(points.len() - window_size) {
        // Calculate incoming direction (average of last few segments)
        let mut in_dx = 0.0f32;
        let mut in_dy = 0.0f32;
        for j in (i - window_size)..i {
            in_dx += (points[j + 1].0 as f32) - (points[j].0 as f32);
            in_dy += (points[j + 1].1 as f32) - (points[j].1 as f32);
        }

        // Calculate outgoing direction (average of next few segments)
        let mut out_dx = 0.0f32;
        let mut out_dy = 0.0f32;
        for j in i..(i + window_size) {
            out_dx += (points[j + 1].0 as f32) - (points[j].0 as f32);
            out_dy += (points[j + 1].1 as f32) - (points[j].1 as f32);
        }

        let angle = angle_between_vectors((in_dx, in_dy), (out_dx, out_dy));

        // If angle change is significant, mark as corner
        if angle > angle_threshold {
            // Make sure we're not too close to another corner
            if corner_indices.is_empty() || i - corner_indices.last().unwrap() >= min_segment_length {
                corner_indices.push(i);
            }
        }
    }

    if corner_indices.is_empty() {
        return vec![path.clone()];
    }

    // Split path at corners
    let mut result = Vec::new();
    let mut start = 0;

    for &corner_idx in &corner_indices {
        if corner_idx > start + min_segment_length {
            let segment_points: Vec<_> = points[start..=corner_idx].to_vec();
            if segment_points.len() >= 2 {
                result.push(RawPath {
                    points: segment_points,
                    is_closed: false,
                });
            }
        }
        start = corner_idx;
    }

    // Add final segment
    if points.len() > start + min_segment_length {
        let segment_points: Vec<_> = points[start..].to_vec();
        if segment_points.len() >= 2 {
            result.push(RawPath {
                points: segment_points,
                is_closed: false,
            });
        }
    }

    if result.is_empty() {
        return vec![path.clone()];
    }

    result
}

/// Trace all paths through the skeleton
/// Returns individual path segments between endpoints/junctions
pub fn trace_paths(skeleton: &[bool], width: usize, height: usize) -> Vec<RawPath> {
    let endpoints = find_endpoints(skeleton, width, height);
    let junctions = find_junctions(skeleton, width, height);

    let mut visited = vec![false; width * height];
    let mut paths = Vec::new();

    // Mark junctions as special (we'll stop at them but can restart from them)
    let junction_set: std::collections::HashSet<(usize, usize)> = junctions.iter().cloned().collect();
    let endpoint_set: std::collections::HashSet<(usize, usize)> = endpoints.iter().cloned().collect();

    // Helper to get unvisited neighbors
    let get_unvisited_neighbors = |x: usize, y: usize, visited: &[bool]| -> Vec<(usize, usize)> {
        let mut neighbors = Vec::new();
        for dy in -1i32..=1 {
            for dx in -1i32..=1 {
                if dy == 0 && dx == 0 {
                    continue;
                }
                let nx = x as i32 + dx;
                let ny = y as i32 + dy;
                if nx >= 0 && nx < width as i32 && ny >= 0 && ny < height as i32 {
                    let nidx = ny as usize * width + nx as usize;
                    if skeleton[nidx] && !visited[nidx] {
                        neighbors.push((nx as usize, ny as usize));
                    }
                }
            }
        }
        neighbors
    };

    // Trace from each endpoint
    for &start in &endpoints {
        let start_idx = start.1 * width + start.0;
        if visited[start_idx] {
            continue;
        }

        let mut path = vec![start];
        visited[start_idx] = true;
        let mut current = start;

        loop {
            let neighbors = get_unvisited_neighbors(current.0, current.1, &visited);

            if neighbors.is_empty() {
                // Check if we can reach another endpoint/junction that's already visited
                // (this handles completing paths at junctions)
                break;
            }

            // Choose next point (prefer continuing in same direction)
            let next = if neighbors.len() == 1 {
                neighbors[0]
            } else {
                // Multiple choices - pick one that continues the path direction
                let prev = if path.len() >= 2 {
                    path[path.len() - 2]
                } else {
                    current
                };
                let dx = current.0 as i32 - prev.0 as i32;
                let dy = current.1 as i32 - prev.1 as i32;

                // Find neighbor most aligned with current direction
                *neighbors.iter()
                    .max_by_key(|&&n| {
                        let ndx = n.0 as i32 - current.0 as i32;
                        let ndy = n.1 as i32 - current.1 as i32;
                        dx * ndx + dy * ndy // Dot product
                    })
                    .unwrap_or(&neighbors[0])
            };

            let next_idx = next.1 * width + next.0;
            visited[next_idx] = true;
            path.push(next);

            // Stop at endpoints or junctions
            if endpoint_set.contains(&next) || junction_set.contains(&next) {
                break;
            }

            current = next;
        }

        if path.len() >= 2 {
            paths.push(RawPath { points: path, is_closed: false });
        }
    }

    // Handle closed curves (no endpoints) - find unvisited skeleton pixels
    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let idx = y * width + x;
            if !skeleton[idx] || visited[idx] {
                continue;
            }

            // Start of unvisited closed curve
            let start = (x, y);
            let mut path = vec![start];
            visited[idx] = true;
            let mut current = start;

            loop {
                let neighbors = get_unvisited_neighbors(current.0, current.1, &visited);

                if neighbors.is_empty() {
                    // Check if we can close the loop back to start
                    let dx = (start.0 as i32 - current.0 as i32).abs();
                    let dy = (start.1 as i32 - current.1 as i32).abs();
                    if dx <= 1 && dy <= 1 && path.len() > 2 {
                        path.push(start); // Close the loop
                    }
                    break;
                }

                let next = neighbors[0];
                let next_idx = next.1 * width + next.0;
                visited[next_idx] = true;
                path.push(next);
                current = next;
            }

            if path.len() >= 3 {
                let is_closed = path.first() == path.last();
                paths.push(RawPath { points: path, is_closed });
            }
        }
    }

    // Also trace from junctions for paths between junctions
    for &start in &junctions {
        let neighbors = get_unvisited_neighbors(start.0, start.1, &visited);
        for neighbor in neighbors {
            let mut path = vec![start, neighbor];
            let neighbor_idx = neighbor.1 * width + neighbor.0;
            visited[neighbor_idx] = true;
            let mut current = neighbor;

            loop {
                let next_neighbors = get_unvisited_neighbors(current.0, current.1, &visited);
                if next_neighbors.is_empty() {
                    break;
                }

                let next = next_neighbors[0];
                let next_idx = next.1 * width + next.0;
                visited[next_idx] = true;
                path.push(next);

                if endpoint_set.contains(&next) || junction_set.contains(&next) {
                    break;
                }

                current = next;
            }

            if path.len() >= 2 {
                paths.push(RawPath { points: path, is_closed: false });
            }
        }
    }

    paths
}

/// Merge short path fragments with nearby longer paths
pub fn merge_short_paths(paths: &mut Vec<RawPath>, min_length: usize, max_gap: f32) {
    // Sort by length (longer first)
    paths.sort_by(|a, b| b.points.len().cmp(&a.points.len()));

    let mut merged_indices = std::collections::HashSet::new();

    for i in 0..paths.len() {
        if merged_indices.contains(&i) || paths[i].points.len() >= min_length {
            continue;
        }

        let short_path = &paths[i];
        let short_start = short_path.points.first().unwrap();
        let short_end = short_path.points.last().unwrap();

        // Find nearest longer path to merge with
        let mut best_target = None;
        let mut best_dist = max_gap + 1.0;

        for j in 0..paths.len() {
            if i == j || merged_indices.contains(&j) || paths[j].points.len() < min_length {
                continue;
            }

            let target = &paths[j];
            let target_start = target.points.first().unwrap();
            let target_end = target.points.last().unwrap();

            // Check distances between endpoints
            let distances = [
                distance(*short_start, *target_start),
                distance(*short_start, *target_end),
                distance(*short_end, *target_start),
                distance(*short_end, *target_end),
            ];

            for &d in &distances {
                if d < best_dist {
                    best_dist = d;
                    best_target = Some(j);
                }
            }
        }

        if let Some(j) = best_target {
            if best_dist <= max_gap {
                merged_indices.insert(i);
                // The target path will absorb the short path's pixels
                // (in practice, we just remove the short path)
            }
        }
    }

    // Remove merged paths
    let mut new_paths = Vec::new();
    for (i, path) in paths.drain(..).enumerate() {
        if !merged_indices.contains(&i) {
            new_paths.push(path);
        }
    }
    *paths = new_paths;
}

fn distance(a: (usize, usize), b: (usize, usize)) -> f32 {
    let dx = a.0 as f32 - b.0 as f32;
    let dy = a.1 as f32 - b.1 as f32;
    (dx * dx + dy * dy).sqrt()
}

/// Order strokes according to writing conventions
/// Primary: top-to-bottom, Secondary: left-to-right
pub fn order_strokes(paths: &mut Vec<RawPath>) {
    paths.sort_by(|a, b| {
        // Get bounding boxes
        let a_min_y = a.points.iter().map(|p| p.1).min().unwrap_or(0);
        let b_min_y = b.points.iter().map(|p| p.1).min().unwrap_or(0);

        let a_min_x = a.points.iter().map(|p| p.0).min().unwrap_or(0);
        let b_min_x = b.points.iter().map(|p| p.0).min().unwrap_or(0);

        // Check if strokes are roughly at same vertical level (within 10% of height)
        let height = std::cmp::max(
            a.points.iter().map(|p| p.1).max().unwrap_or(0),
            b.points.iter().map(|p| p.1).max().unwrap_or(0)
        );
        let threshold = (height as f32 * 0.15) as usize;

        if (a_min_y as i32 - b_min_y as i32).abs() <= threshold as i32 {
            // Same level, sort left-to-right
            a_min_x.cmp(&b_min_x)
        } else {
            // Different levels, sort top-to-bottom
            a_min_y.cmp(&b_min_y)
        }
    });
}

/// Catmull-Rom spline interpolation
fn catmull_rom(p0: (f32, f32), p1: (f32, f32), p2: (f32, f32), p3: (f32, f32), t: f32) -> (f32, f32) {
    let t2 = t * t;
    let t3 = t2 * t;

    let x = 0.5 * ((2.0 * p1.0) +
                   (-p0.0 + p2.0) * t +
                   (2.0 * p0.0 - 5.0 * p1.0 + 4.0 * p2.0 - p3.0) * t2 +
                   (-p0.0 + 3.0 * p1.0 - 3.0 * p2.0 + p3.0) * t3);

    let y = 0.5 * ((2.0 * p1.1) +
                   (-p0.1 + p2.1) * t +
                   (2.0 * p0.1 - 5.0 * p1.1 + 4.0 * p2.1 - p3.1) * t2 +
                   (-p0.1 + 3.0 * p1.1 - 3.0 * p2.1 + p3.1) * t3);

    (x, y)
}

/// Smooth a path using Catmull-Rom splines
/// Returns approximately target_points points (default ~50)
pub fn smooth_path(points: &[(usize, usize)], target_points: usize) -> Vec<(f32, f32)> {
    if points.len() < 2 {
        return points.iter().map(|&(x, y)| (x as f32, y as f32)).collect();
    }

    if points.len() == 2 {
        // Just linear interpolation for 2 points
        let (x0, y0) = (points[0].0 as f32, points[0].1 as f32);
        let (x1, y1) = (points[1].0 as f32, points[1].1 as f32);
        return (0..target_points)
            .map(|i| {
                let t = i as f32 / (target_points - 1) as f32;
                (x0 + t * (x1 - x0), y0 + t * (y1 - y0))
            })
            .collect();
    }

    // Convert to f32
    let pts: Vec<(f32, f32)> = points.iter().map(|&(x, y)| (x as f32, y as f32)).collect();

    // Calculate total path length for even distribution
    let mut total_length = 0.0;
    for i in 1..pts.len() {
        let dx = pts[i].0 - pts[i - 1].0;
        let dy = pts[i].1 - pts[i - 1].1;
        total_length += (dx * dx + dy * dy).sqrt();
    }

    if total_length < 0.001 {
        return pts;
    }

    // Interpolate using Catmull-Rom
    let segments = pts.len() - 1;
    let points_per_segment = (target_points / segments).max(2);
    let mut result = Vec::with_capacity(target_points);

    for i in 0..segments {
        let p0 = if i > 0 { pts[i - 1] } else { pts[0] };
        let p1 = pts[i];
        let p2 = pts[i + 1];
        let p3 = if i + 2 < pts.len() { pts[i + 2] } else { pts[pts.len() - 1] };

        for j in 0..points_per_segment {
            let t = j as f32 / points_per_segment as f32;
            result.push(catmull_rom(p0, p1, p2, p3, t));
        }
    }

    // Always include the last point
    result.push(*pts.last().unwrap());

    // Remove duplicate consecutive points
    result.dedup_by(|a, b| (a.0 - b.0).abs() < 0.5 && (a.1 - b.1).abs() < 0.5);

    result
}

/// Infer stroke direction based on geometry
pub fn infer_direction(points: &[(f32, f32)]) -> String {
    if points.len() < 2 {
        return "down".to_string();
    }

    let start = points[0];
    let end = *points.last().unwrap();

    let dx = end.0 - start.0;
    let dy = end.1 - start.1;
    let dist = (dx * dx + dy * dy).sqrt();

    if dist < 1.0 {
        return "down".to_string();
    }

    // Calculate how straight the path is (using least squares deviation)
    let is_curved = calculate_curvature(points) > 0.15;

    // Get angle
    let angle = dy.atan2(dx).to_degrees();

    if is_curved {
        // Determine curve direction by analyzing curvature sign
        let curvature_sign = calculate_curvature_sign(points);

        if angle.abs() > 135.0 || angle.abs() < 45.0 {
            // Roughly horizontal curve
            if curvature_sign > 0.0 {
                return "curve-left".to_string();
            } else {
                return "curve-right".to_string();
            }
        } else {
            // Roughly vertical curve
            if dy > 0.0 {
                return "down-curve".to_string();
            } else {
                return "up-curve".to_string();
            }
        }
    }

    // Straight stroke direction
    let norm_angle = if angle < 0.0 { angle + 360.0 } else { angle };

    match norm_angle {
        a if a <= 22.5 || a > 337.5 => "right".to_string(),
        a if a > 22.5 && a <= 67.5 => "down-right".to_string(),
        a if a > 67.5 && a <= 112.5 => "down".to_string(),
        a if a > 112.5 && a <= 157.5 => "down-left".to_string(),
        a if a > 157.5 && a <= 202.5 => "left".to_string(),
        a if a > 202.5 && a <= 247.5 => "up-left".to_string(),
        a if a > 247.5 && a <= 292.5 => "up".to_string(),
        a if a > 292.5 && a <= 337.5 => "up-right".to_string(),
        _ => "down".to_string(),
    }
}

/// Calculate path curvature (0 = straight, higher = more curved)
fn calculate_curvature(points: &[(f32, f32)]) -> f32 {
    if points.len() < 3 {
        return 0.0;
    }

    // Fit a line using least squares and measure deviation
    let n = points.len() as f32;
    let sum_x: f32 = points.iter().map(|p| p.0).sum();
    let sum_y: f32 = points.iter().map(|p| p.1).sum();
    let sum_xx: f32 = points.iter().map(|p| p.0 * p.0).sum();
    let sum_xy: f32 = points.iter().map(|p| p.0 * p.1).sum();

    let denom = n * sum_xx - sum_x * sum_x;
    if denom.abs() < 0.001 {
        // Vertical line - check horizontal deviation
        let avg_x = sum_x / n;
        let deviation: f32 = points.iter().map(|p| (p.0 - avg_x).abs()).sum::<f32>() / n;
        let range_y = points.iter().map(|p| p.1).fold(f32::MIN, f32::max)
            - points.iter().map(|p| p.1).fold(f32::MAX, f32::min);
        return deviation / range_y.max(1.0);
    }

    let m = (n * sum_xy - sum_x * sum_y) / denom;
    let b = (sum_y - m * sum_x) / n;

    // Calculate average distance from line
    let deviation: f32 = points.iter()
        .map(|p| {
            let predicted_y = m * p.0 + b;
            (p.1 - predicted_y).abs()
        })
        .sum::<f32>() / n;

    // Normalize by path length
    let path_len = {
        let mut len = 0.0;
        for i in 1..points.len() {
            let dx = points[i].0 - points[i - 1].0;
            let dy = points[i].1 - points[i - 1].1;
            len += (dx * dx + dy * dy).sqrt();
        }
        len
    };

    deviation / path_len.max(1.0)
}

/// Calculate curvature sign (positive = curves left/up, negative = curves right/down)
fn calculate_curvature_sign(points: &[(f32, f32)]) -> f32 {
    if points.len() < 3 {
        return 0.0;
    }

    // Use cross product of consecutive segments
    let mut total_cross = 0.0;
    for i in 1..points.len() - 1 {
        let v1 = (points[i].0 - points[i - 1].0, points[i].1 - points[i - 1].1);
        let v2 = (points[i + 1].0 - points[i].0, points[i + 1].1 - points[i].1);
        total_cross += v1.0 * v2.1 - v1.1 * v2.0;
    }

    total_cross
}

/// Ensure correct stroke direction based on writing conventions
fn ensure_correct_direction(path: &mut RawPath) {
    if path.points.len() < 2 {
        return;
    }

    let start = path.points.first().unwrap();
    let end = path.points.last().unwrap();

    // For closed paths, find topmost point and rotate to start there
    if path.is_closed {
        let top_idx = path.points.iter()
            .enumerate()
            .min_by_key(|(_, p)| p.1)
            .map(|(i, _)| i)
            .unwrap_or(0);

        // Rotate points so topmost is first
        let mut rotated = Vec::with_capacity(path.points.len());
        for i in 0..path.points.len() {
            rotated.push(path.points[(top_idx + i) % path.points.len()]);
        }
        path.points = rotated;
        return;
    }

    // For open paths, ensure direction follows conventions
    let should_reverse = if (start.1 as i32 - end.1 as i32).abs() > 10 {
        // Vertical-ish stroke: should go top-to-bottom
        start.1 > end.1
    } else if (start.0 as i32 - end.0 as i32).abs() > 10 {
        // Horizontal-ish stroke: should go left-to-right
        start.0 > end.0
    } else {
        // Short stroke - use diagonal preference (top-left to bottom-right)
        start.1 > end.1 || (start.1 == end.1 && start.0 > end.0)
    };

    if should_reverse {
        path.points.reverse();
    }
}

/// Main entry point: extract strokes from a font glyph
pub fn extract_strokes(font_data: &[u8], character: char, size: u32) -> Result<StrokeData, String> {
    // Parse font
    let font = Font::try_from_bytes(font_data)
        .ok_or("Failed to parse font data")?;

    // Render glyph to grayscale image
    let mut img: GrayImage = ImageBuffer::from_pixel(size, size, Luma([255u8]));
    let font_size = size as f32 * 0.75;
    let scale = Scale::uniform(font_size);

    // Get glyph metrics for centering
    let glyph = font.glyph(character).scaled(scale).positioned(point(0.0, 0.0));

    if let Some(bb) = glyph.pixel_bounding_box() {
        let glyph_width = bb.max.x - bb.min.x;
        let glyph_height = bb.max.y - bb.min.y;

        let x_offset = ((size as i32 - glyph_width) / 2) - bb.min.x;
        let y_offset = ((size as i32 - glyph_height) / 2) - bb.min.y;

        let glyph = font.glyph(character)
            .scaled(scale)
            .positioned(point(x_offset as f32, y_offset as f32));

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

    // Convert to binary (threshold)
    let binary: Vec<bool> = img.pixels()
        .map(|p| p.0[0] < 180)
        .collect();

    // Skeletonize
    let mut skeleton = skeletonize(&binary, size as usize, size as usize);

    // Bridge small gaps
    bridge_gaps(&mut skeleton, size as usize, size as usize, 3);

    // Prune short branches (noise)
    prune_branches(&mut skeleton, size as usize, size as usize, 3, 0.15);

    // Trace paths through skeleton
    let traced_paths = trace_paths(&skeleton, size as usize, size as usize);

    // Split paths at sharp corners (angle > 100 degrees)
    // Only split at very sharp turns to reduce fragmentation
    let mut paths: Vec<RawPath> = traced_paths
        .iter()
        .flat_map(|p| split_at_corners(p, 100.0, 8))
        .collect();

    // Merge short fragments (less than 15 pixels) that are close together
    // More aggressive merging to produce fewer, more coherent strokes
    merge_short_paths(&mut paths, 15, 8.0);

    // Filter out very short paths (noise)
    paths.retain(|p| p.points.len() >= 5);

    // Ensure correct direction for each path
    for path in &mut paths {
        ensure_correct_direction(path);
    }

    // Order strokes
    order_strokes(&mut paths);

    // Convert to output format
    let strokes: Vec<Stroke> = paths.iter().map(|path| {
        // Smooth the path
        let smooth_points = smooth_path(&path.points, 50);

        // Normalize to 0-100 coordinate space
        let scale = 100.0 / size as f32;
        let normalized: Vec<[f32; 2]> = smooth_points.iter()
            .map(|&(x, y)| [x * scale, y * scale])
            .collect();

        // Get start and end points (copy values to avoid borrow issues)
        let (start_x, start_y) = if let Some(p) = normalized.first() {
            (p[0], p[1])
        } else {
            (50.0, 50.0)
        };

        let (end_x, end_y) = if let Some(p) = normalized.last() {
            (p[0], p[1])
        } else {
            (50.0, 50.0)
        };

        let direction = infer_direction(&smooth_points.iter()
            .map(|&(x, y)| (x * scale, y * scale))
            .collect::<Vec<_>>());

        Stroke {
            points: normalized,
            start_zone: StrokeZone {
                cx: start_x,
                cy: start_y,
                r: 10.0, // Default radius in 0-100 space
            },
            end_zone: StrokeZone {
                cx: end_x,
                cy: end_y,
                r: 10.0,
            },
            direction,
        }
    }).collect();

    // Determine character type
    let char_type = if character.is_ascii_uppercase() {
        "uppercase".to_string()
    } else if character.is_ascii_lowercase() {
        "lowercase".to_string()
    } else if character.is_ascii_digit() {
        "number".to_string()
    } else {
        "symbol".to_string()
    };

    Ok(StrokeData {
        character: character.to_string(),
        font: "dynamic".to_string(),
        char_type,
        strokes,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_connected_components_simple() {
        // 5x5 grid with two separate components
        let mut binary = vec![false; 25];
        // Component 1: top-left corner
        binary[0] = true;
        binary[1] = true;
        binary[5] = true;
        // Component 2: bottom-right corner
        binary[23] = true;
        binary[24] = true;

        let (labels, count) = connected_components(&binary, 5, 5);

        assert_eq!(count, 2);
        // First component should have same label
        assert_eq!(labels[0], labels[1]);
        assert_eq!(labels[0], labels[5]);
        // Second component should have different label
        assert_eq!(labels[23], labels[24]);
        assert_ne!(labels[0], labels[23]);
    }

    #[test]
    fn test_connected_components_single() {
        // 5x5 grid with one connected component
        let mut binary = vec![false; 25];
        // L-shape
        binary[0] = true;
        binary[5] = true;
        binary[10] = true;
        binary[11] = true;
        binary[12] = true;

        let (labels, count) = connected_components(&binary, 5, 5);

        assert_eq!(count, 1);
        assert!(labels.iter().filter(|&&l| l != 0).all(|&l| l == 1));
    }

    #[test]
    fn test_catmull_rom_midpoint() {
        // For p1 = (0, 0), p2 = (2, 0), t = 0.5 should give approximately (1, 0)
        let p0 = (-1.0, 0.0);
        let p1 = (0.0, 0.0);
        let p2 = (2.0, 0.0);
        let p3 = (3.0, 0.0);

        let mid = catmull_rom(p0, p1, p2, p3, 0.5);

        assert!((mid.0 - 1.0).abs() < 0.1);
        assert!(mid.1.abs() < 0.1);
    }

    #[test]
    fn test_smooth_path_preserves_endpoints() {
        let points = vec![(0, 0), (10, 10), (20, 0)];
        let smoothed = smooth_path(&points, 20);

        assert!((smoothed[0].0 - 0.0).abs() < 0.1);
        assert!((smoothed[0].1 - 0.0).abs() < 0.1);

        let last = smoothed.last().unwrap();
        assert!((last.0 - 20.0).abs() < 0.1);
        assert!((last.1 - 0.0).abs() < 0.1);
    }

    #[test]
    fn test_infer_direction_vertical() {
        let points = vec![(50.0, 10.0), (50.0, 50.0), (50.0, 90.0)];
        let dir = infer_direction(&points);
        assert_eq!(dir, "down");
    }

    #[test]
    fn test_infer_direction_horizontal() {
        let points = vec![(10.0, 50.0), (50.0, 50.0), (90.0, 50.0)];
        let dir = infer_direction(&points);
        assert_eq!(dir, "right");
    }

    #[test]
    fn test_infer_direction_diagonal() {
        let points = vec![(10.0, 10.0), (50.0, 50.0), (90.0, 90.0)];
        let dir = infer_direction(&points);
        assert_eq!(dir, "down-right");
    }

    #[test]
    fn test_calculate_curvature_straight() {
        let points = vec![(0.0, 0.0), (10.0, 10.0), (20.0, 20.0)];
        let curvature = calculate_curvature(&points);
        assert!(curvature < 0.1);
    }

    #[test]
    fn test_calculate_curvature_curved() {
        // Arc-like curve
        let points = vec![
            (0.0, 50.0), (10.0, 20.0), (50.0, 0.0), (90.0, 20.0), (100.0, 50.0)
        ];
        let curvature = calculate_curvature(&points);
        assert!(curvature > 0.1);
    }

    #[test]
    fn test_order_strokes() {
        let mut paths = vec![
            RawPath { points: vec![(50, 80), (50, 90)], is_closed: false }, // Bottom
            RawPath { points: vec![(50, 10), (50, 30)], is_closed: false }, // Top
            RawPath { points: vec![(80, 50), (90, 50)], is_closed: false }, // Right middle
            RawPath { points: vec![(10, 50), (30, 50)], is_closed: false }, // Left middle
        ];

        order_strokes(&mut paths);

        // Top stroke should be first
        assert_eq!(paths[0].points[0].1, 10);
        // Left middle should come before right middle (same Y level)
        let middle_strokes: Vec<_> = paths.iter()
            .filter(|p| p.points[0].1 == 50)
            .collect();
        if middle_strokes.len() >= 2 {
            assert!(middle_strokes[0].points[0].0 < middle_strokes[1].points[0].0);
        }
    }

    #[test]
    fn test_merge_short_paths() {
        let mut paths = vec![
            RawPath { points: vec![(0, 0), (10, 0), (20, 0), (30, 0), (40, 0),
                                   (50, 0), (60, 0), (70, 0), (80, 0), (90, 0)], is_closed: false },
            RawPath { points: vec![(95, 0), (97, 0)], is_closed: false }, // Short, near the long one
        ];

        merge_short_paths(&mut paths, 5, 10.0);

        // Short path should be merged
        assert_eq!(paths.len(), 1);
    }

    #[test]
    fn test_find_junctions_t_shape() {
        // Create a T-shape skeleton with clean connections (no diagonals)
        // Using a larger grid to avoid edge effects
        let mut skeleton = vec![false; 81]; // 9x9
        // Horizontal line at y=4
        skeleton[37] = true; // (1, 4)
        skeleton[38] = true; // (2, 4)
        skeleton[39] = true; // (3, 4)
        skeleton[40] = true; // (4, 4) - junction point
        skeleton[41] = true; // (5, 4)
        skeleton[42] = true; // (6, 4)
        skeleton[43] = true; // (7, 4)
        // Vertical line from junction going up
        skeleton[13] = true; // (4, 1)
        skeleton[22] = true; // (4, 2)
        skeleton[31] = true; // (4, 3)
        // skeleton[40] is the junction point (4, 4)

        let junctions = find_junctions(&skeleton, 9, 9);

        // The junction point should have exactly 3 neighbors
        assert!(junctions.contains(&(4, 4)), "Junction at (4,4) should be found");
    }
}
