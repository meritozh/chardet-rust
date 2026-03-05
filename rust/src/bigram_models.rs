//! Bigram model loading and scoring for statistical detection.

use std::collections::HashMap;
use once_cell::sync::Lazy;
use std::sync::Mutex;

/// Size of the bigram lookup table (256 * 256)
const BIGRAM_TABLE_SIZE: usize = 65536;

/// Weight applied to non-ASCII bigrams
pub const NON_ASCII_BIGRAM_WEIGHT: i32 = 8;

/// Cached models
static MODELS: Lazy<Mutex<Option<HashMap<String, Vec<u8>>>>> = Lazy::new(|| {
    Mutex::new(None)
});

/// Load bigram models from models.bin file content
pub fn load_models(data: &[u8]) -> Result<HashMap<String, Vec<u8>>, String> {
    let mut models = HashMap::new();
    let mut offset = 0;
    
    if data.len() < 4 {
        return Err("models.bin too small".to_string());
    }
    
    // Read number of encodings (big-endian u32)
    let num_encodings = u32::from_be_bytes([data[0], data[1], data[2], data[3]]) as usize;
    offset += 4;
    
    if num_encodings > 10000 {
        return Err(format!("corrupt models.bin: num_encodings={} exceeds limit", num_encodings));
    }
    
    for _ in 0..num_encodings {
        // Read name length
        if offset + 4 > data.len() {
            return Err("truncated models.bin".to_string());
        }
        let name_len = u32::from_be_bytes([data[offset], data[offset+1], data[offset+2], data[offset+3]]) as usize;
        offset += 4;
        
        if name_len > 256 {
            return Err(format!("corrupt models.bin: name_len={} exceeds 256", name_len));
        }
        
        // Read name
        if offset + name_len > data.len() {
            return Err("truncated models.bin".to_string());
        }
        let name = String::from_utf8(data[offset..offset + name_len].to_vec())
            .map_err(|e| format!("invalid UTF-8 in model name: {}", e))?;
        offset += name_len;
        
        // Read number of entries
        if offset + 4 > data.len() {
            return Err("truncated models.bin".to_string());
        }
        let num_entries = u32::from_be_bytes([data[offset], data[offset+1], data[offset+2], data[offset+3]]) as usize;
        offset += 4;
        
        if num_entries > BIGRAM_TABLE_SIZE {
            return Err(format!("corrupt models.bin: num_entries={} exceeds {}", num_entries, BIGRAM_TABLE_SIZE));
        }
        
        // Create table and fill with weights
        let mut table = vec![0u8; BIGRAM_TABLE_SIZE];
        for _ in 0..num_entries {
            if offset + 3 > data.len() {
                return Err("truncated models.bin".to_string());
            }
            let b1 = data[offset] as usize;
            let b2 = data[offset + 1] as usize;
            let weight = data[offset + 2];
            offset += 3;
            table[(b1 << 8) | b2] = weight;
        }
        
        models.insert(name, table);
    }
    
    Ok(models)
}

/// Initialize models from embedded data
pub fn init_models(data: &[u8]) -> Result<(), String> {
    let models = load_models(data)?;
    let mut cache = MODELS.lock().unwrap();
    *cache = Some(models);
    Ok(())
}

/// Get a model by key (e.g., "French/windows-1252")
pub fn get_model(key: &str) -> Option<Vec<u8>> {
    let cache = MODELS.lock().unwrap();
    cache.as_ref()?.get(key).cloned()
}

/// Check if models are loaded
pub fn models_loaded() -> bool {
    let cache = MODELS.lock().unwrap();
    cache.is_some()
}

/// Get all model keys for a given encoding
pub fn get_models_for_encoding(encoding: &str) -> Vec<(String, Vec<u8>)> {
    let cache = MODELS.lock().unwrap();
    let models = match cache.as_ref() {
        Some(m) => m,
        None => return vec![],
    };
    
    models
        .iter()
        .filter(|(k, _)| k.contains(&format!("/{}", encoding)))
        .map(|(k, v)| (k.clone(), v.clone()))
        .collect()
}

/// Calculate L2 norm of a model
pub fn calculate_model_norm(model: &[u8]) -> f64 {
    let sq_sum: u64 = model.iter().map(|&w| (w as u64) * (w as u64)).sum();
    (sq_sum as f64).sqrt()
}

/// Score data against a model using cosine similarity
pub fn score_with_model(data: &[u8], model: &[u8], model_norm: f64) -> f64 {
    if data.len() < 2 || model_norm == 0.0 {
        return 0.0;
    }
    
    // Build weighted frequency profile
    let mut profile: HashMap<u16, i32> = HashMap::new();
    let mut total_weight = 0;
    
    for i in 0..data.len() - 1 {
        let b1 = data[i];
        let b2 = data[i + 1];
        let idx = ((b1 as u16) << 8) | (b2 as u16);
        
        let weight = if b1 > 0x7F || b2 > 0x7F {
            NON_ASCII_BIGRAM_WEIGHT
        } else {
            1
        };
        
        *profile.entry(idx).or_insert(0) += weight;
        total_weight += weight;
    }
    
    if total_weight == 0 {
        return 0.0;
    }
    
    // Calculate input norm and dot product
    let mut input_norm_sq = 0i64;
    let mut dot_product = 0i64;
    
    for (idx, weight) in &profile {
        let model_weight = model[*idx as usize] as i64;
        let w = *weight as i64;
        input_norm_sq += w * w;
        dot_product += model_weight * w;
    }
    
    let input_norm = (input_norm_sq as f64).sqrt();
    if input_norm == 0.0 {
        return 0.0;
    }
    
    dot_product as f64 / (model_norm * input_norm)
}

/// Score data against all language variants of an encoding
pub fn score_best_language(data: &[u8], encoding: &str) -> (f64, Option<String>) {
    let models = get_models_for_encoding(encoding);
    if models.is_empty() {
        return (0.0, None);
    }
    
    let mut best_score = 0.0;
    let mut best_lang = None;
    
    for (key, model) in models {
        let norm = calculate_model_norm(&model);
        let score = score_with_model(data, &model, norm);
        
        // Extract language from key (format: "Language/encoding")
        let lang = key.split('/').next().map(|s| s.to_string());
        
        if score > best_score {
            best_score = score;
            best_lang = lang;
        }
    }
    
    (best_score, best_lang)
}

/// Pre-computed model norms cache
static MODEL_NORMS: Lazy<Mutex<HashMap<String, f64>>> = Lazy::new(|| {
    Mutex::new(HashMap::new())
});

/// Get cached model norm or compute it
pub fn get_model_norm(key: &str) -> Option<f64> {
    // Check cache first
    {
        let norms = MODEL_NORMS.lock().unwrap();
        if let Some(&norm) = norms.get(key) {
            return Some(norm);
        }
    }
    
    // Compute and cache
    let model = get_model(key)?;
    let norm = calculate_model_norm(&model);
    
    let mut norms = MODEL_NORMS.lock().unwrap();
    norms.insert(key.to_string(), norm);
    
    Some(norm)
}
