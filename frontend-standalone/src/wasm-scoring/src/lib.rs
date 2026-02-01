//! WASM Scoring Engine for Learning Letters
//!
//! This module provides image-based scoring for handwritten characters,
//! comparing user drawings against reference images generated from fonts.

mod scoring;
mod image_ops;

use wasm_bindgen::prelude::*;
use serde::{Serialize, Deserialize};

#[wasm_bindgen(start)]
pub fn init() {
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

/// Result of scoring a drawing
#[derive(Serialize, Deserialize)]
pub struct ScoringResult {
    pub score: u8,
    pub stars: u8,
    pub feedback: String,
    pub coverage: f32,
    pub accuracy: f32,
    pub similarity: f32,
}

#[wasm_bindgen]
pub struct WasmScoringResult {
    inner: ScoringResult,
    reference_image: Vec<u8>,
}

#[wasm_bindgen]
impl WasmScoringResult {
    #[wasm_bindgen(getter)]
    pub fn score(&self) -> u8 {
        self.inner.score
    }

    #[wasm_bindgen(getter)]
    pub fn stars(&self) -> u8 {
        self.inner.stars
    }

    #[wasm_bindgen(getter)]
    pub fn feedback(&self) -> String {
        self.inner.feedback.clone()
    }

    #[wasm_bindgen(getter)]
    pub fn coverage(&self) -> f32 {
        self.inner.coverage
    }

    #[wasm_bindgen(getter)]
    pub fn accuracy(&self) -> f32 {
        self.inner.accuracy
    }

    #[wasm_bindgen(getter)]
    pub fn similarity(&self) -> f32 {
        self.inner.similarity
    }

    #[wasm_bindgen(getter)]
    pub fn reference_image(&self) -> Vec<u8> {
        self.reference_image.clone()
    }
}

/// Score a user's drawing against a reference character
///
/// # Arguments
/// * `image_data` - PNG image bytes of the user's drawing
/// * `character` - The character that was drawn (e.g., 'A', 'a', '5')
/// * `font_data` - TTF font bytes to use for generating the reference
///
/// # Returns
/// A ScoringResult containing the score, stars, and detailed metrics
#[wasm_bindgen]
pub fn score_drawing(
    image_data: &[u8],
    character: &str,
    font_data: &[u8],
) -> Result<WasmScoringResult, JsValue> {
    let char = character.chars().next()
        .ok_or_else(|| JsValue::from_str("Empty character string"))?;

    let result = scoring::score_drawing_internal(image_data, char, font_data)
        .map_err(|e| JsValue::from_str(&e))?;

    Ok(result)
}

/// Generate a reference image for a character
///
/// # Arguments
/// * `character` - The character to render
/// * `font_data` - TTF font bytes
/// * `size` - Output image size (width and height)
///
/// # Returns
/// PNG image bytes
#[wasm_bindgen]
pub fn generate_reference_image(
    character: &str,
    font_data: &[u8],
    size: u32,
) -> Result<Vec<u8>, JsValue> {
    let char = character.chars().next()
        .ok_or_else(|| JsValue::from_str("Empty character string"))?;

    scoring::generate_reference_image_internal(char, font_data, size)
        .map_err(|e| JsValue::from_str(&e))
}
