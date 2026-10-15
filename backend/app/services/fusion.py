def fuse(text_category, text_score, vision_score):
    # OCR text is already classified with speech. Missing generic visual cues
    # must not dilute strong semantic evidence, including silent videos.
    text_score = max(0.0, min(1.0, text_score))
    vision_score = max(0.0, min(1.0, vision_score))
    final_score = text_score + (1 - text_score) * vision_score * 0.3

    if final_score > 1:
        final_score = 1

    final_score = round(final_score, 2)

    if final_score < 0.3 or text_category == "none":
        final_category = "none"
        if final_score > 0.29:
            final_score = 0.29
    else:
        final_category = text_category

    return final_category, final_score
