def borderify_text(text, current_layer, sep):
    if current_layer == 0:
        return sep + "  " + text + "  " + sep

    inner_text = borderify_text(text, current_layer - 1, sep)

    lines = inner_text.split("\n")
    column_width = len(lines[0]) + 2
    horizontal_border = sep * column_width

    new_text = horizontal_border
    for line in lines:
        new_text += "\n" + sep + line + sep
    new_text += "\n" + horizontal_border

    return new_text

print(borderify_text("Hello, world!", 1, '-'))
print()
print(borderify_text("Hello, world!", 2, '-'))
print()
print(borderify_text("Hello, world!", 3, '-'))
