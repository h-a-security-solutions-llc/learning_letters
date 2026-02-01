/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// WASM module types
declare module '../wasm-pkg/learning_letters_scoring.js' {
  export function init(): Promise<void>
  export default init

  export interface WasmScoringResult {
    score: number
    stars: number
    feedback: string
    coverage: number
    accuracy: number
    similarity: number
    reference_image: Uint8Array
  }

  export function score_drawing(
    image_data: Uint8Array,
    character: string,
    font_data: Uint8Array
  ): WasmScoringResult

  export function generate_reference_image(
    character: string,
    font_data: Uint8Array,
    size: number
  ): Uint8Array
}
