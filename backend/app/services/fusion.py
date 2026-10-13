def fuse(text_category, text_score, vision_score):
    final_score = text_score * 0.7 + vision_score * 0.3

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
