//! Universal character encoding detector - Pure Rust implementation
//!
//! This is a port of the chardet Python library to Rust.
//! Provides encoding detection for text files and byte streams.

pub mod bigram_models;
pub mod detector;
pub mod enums;
pub mod equivalences;
pub mod equivalences_full;
pub mod models;
pub mod pipeline;
pub mod registry;

// Re-export core types for convenience
pub use detector::{detect_all_bytes, detect_bytes};
pub use enums::EncodingEra;
pub use pipeline::DetectionResult;