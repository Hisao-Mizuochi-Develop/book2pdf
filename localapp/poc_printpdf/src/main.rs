use printpdf::*;
use std::fs::File;
use std::io::BufWriter;
use std::io::Cursor;

fn main() {
    let img_path = std::env::args().nth(1).expect("Usage: poc_printpdf <image_path>");

    let (doc, page1, layer1) =
        PdfDocument::new("Image to PDF POC", Mm(210.0), Mm(297.0), "Layer 1");
    let current_layer = doc.get_page(page1).get_layer(layer1);

    // Load image via decoder (matching printpdf 0.7 example pattern)
    let image_bytes = std::fs::read(&img_path).expect("Failed to read image");
    let mut cursor = Cursor::new(&image_bytes);

    // Determine decoder based on extension; default to PNG
    let ext = std::path::Path::new(&img_path)
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("png")
        .to_lowercase();

    let image = match ext.as_str() {
        "png" => {
            let decoder = image_crate::codecs::png::PngDecoder::new(&mut cursor).expect("PNG decode error");
            Image::try_from(decoder).expect("printpdf Image from PNG")
        }
        "jpg" | "jpeg" => {
            let decoder = image_crate::codecs::jpeg::JpegDecoder::new(&mut cursor).expect("JPEG decode error");
            Image::try_from(decoder).expect("printpdf Image from JPEG")
        }
        _ => panic!("Unsupported image format: {}", ext),
    };

    let img_w = image.image.width.0 as f32;
    let img_h = image.image.height.0 as f32;
    println!("Image dimensions: {}x{}", img_w, img_h);

    // Calculate scale to fit within A4 with margins (10mm each side)
    let margin = Mm(10.0);
    let max_w = Mm(210.0 - margin.0 * 2.0);
    let max_h = Mm(297.0 - margin.0 * 2.0);

    // Assume 300 DPI for mm calculation: 1 inch = 25.4mm = 300px
    let img_w_mm = img_w * 25.4 / 300.0;
    let img_h_mm = img_h * 25.4 / 300.0;

    let scale_x = max_w.0 / img_w_mm;
    let scale_y = max_h.0 / img_h_mm;
    let scale = scale_x.min(scale_y).min(1.0);

    let final_w = img_w_mm * scale;
    let final_h = img_h_mm * scale;

    // Center the image
    let x = margin + Mm((max_w.0 - final_w) / 2.0);
    let y = margin + Mm((max_h.0 - final_h) / 2.0);

    println!("Placing image at ({:?}, {:?}) scale={}", x, y, scale);

    image.add_to_layer(
        current_layer.clone(),
        ImageTransform {
            translate_x: Some(x),
            translate_y: Some(y),
            scale_x: Some(scale),
            scale_y: Some(scale),
            ..Default::default()
        },
    );

    doc.save(&mut BufWriter::new(File::create("/tmp/poc_printpdf_output.pdf").unwrap()))
        .unwrap();
    println!("Saved to /tmp/poc_printpdf_output.pdf");
}
