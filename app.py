from disney_tips import *
import gradio as gr
from fpdf import FPDF
import tempfile
import os

TAG_LABEL_TO_KEY = {
    "👶 Has Children": "tag_has_children",
    "🧑‍🎓 Has Teenagers": "tag_has_teenagers",
    "♿ Needs Guest Services": "tag_needs_guest_services",
    "🧠 Needs Accommodations (Sensory or Special Needs)": "tag_needs_accommodations",
    "🔇 Prefers Quiet/Calm Spaces": "tag_prefers_quiet",
    "📈 Visiting in Peak Season": "tag_peak_season_visitor",
    "🌅 Early or Late Arrival": "tag_early_or_late_arrival",
    "🌍 International Visitor": "tag_international_visitor",
    "🎉 Attending Special Event": "tag_special_event_attendee",
    "💰 Budget Conscious": "tag_budget_conscious",
    "🥗 Dietary Restrictions": "tag_dietary_restrictions",
    "🎢 Thrill Seeker": "tag_thrill_seeker",
    "🍽️ Foodie Focus": "tag_foodie_focus",
    "😌 Relaxed Rider": "tag_relaxed_rider",
    "👀 First Time Visitor": "tag_first_time_visitor",
    "🔄 Frequent Visitor": "tag_frequent_visitor",
    "🗓️ Planner": "tag_planner",
    "🌊 Goes With The Flow": "tag_go_with_the_flow",
    "☀️ Weather Sensitive": "tag_weather_sensitive",
    "🛑 Needs Rest Breaks": "tag_needs_rest_breaks"
}

def display_top_similar_reviews(top_reviews):
    if top_reviews.empty:
        return "🙁 Sorry! We couldn’t find any matching reviews. Try selecting fewer or different tags."

    output_lines = []

    for idx, row in top_reviews.iterrows():
        tags = []
        if row.get('tag_has_children'): tags.append("With Kids")
        if row.get('tag_has_teenagers'): tags.append("With Teenagers")
        if row.get('tag_needs_guest_services'): tags.append("Guest Services Used")
        if row.get('tag_needs_accommodations'): tags.append("Sensory or Special Needs Support")
        if row.get('tag_prefers_quiet'): tags.append("Prefers Calm Spaces")
        if row.get('tag_peak_season_visitor'): tags.append("Peak Season Visitor")
        if row.get('tag_early_or_late_arrival'): tags.append("Early or Late Arrival")
        if row.get('tag_budget_conscious'): tags.append("Budget Conscious")
        if row.get('tag_dietary_restrictions'): tags.append("Dietary Restrictions")
        if row.get('tag_foodie_focus'): tags.append("Foodie Focus")
        if row.get('tag_thrill_seeker'): tags.append("Thrill Seeker")
        if row.get('tag_relaxed_rider'): tags.append("Relaxed Rider")
        if row.get('tag_first_time_visitor'): tags.append("First Time Visitor")
        if row.get('tag_frequent_visitor'): tags.append("Frequent Visitor")
        if row.get('tag_planner'): tags.append("🗓️ Planner")
        if row.get('tag_go_with_the_flow'): tags.append("Goes With The Flow")
        if row.get('tag_weather_sensitive'): tags.append("Weather Sensitive")
        if row.get('tag_needs_rest_breaks'): tags.append("Needs Rest Breaks")
        if row.get('tag_international_visitor'): tags.append("Visited from Abroad")
        if row.get('tag_special_event_attendee'): tags.append("Attending Special Event")
        if not tags:
            tags.append("👤 General Guest")

        tldr = extract_summary_tfidf(row['Review_Text'], num_sentences=2)
        summary = summarize_review_bullets(row['Review_Text'], num_sentences=3)

        output_lines.append(f"## 📅 Visited {row['Month_Name']} {row['Year']} {' | '.join(tags)}\n")
        output_lines.append(f"**📝 TL;DR:** {tldr}\n")
        output_lines.append(summary)
        output_lines.append("")

    return "\n".join(output_lines)

def gradio_review_recommender(month, year, clusters, selected_tags):
    month_number = {
        "January":1, "February":2, "March":3, "April":4, "May":5, "June":6,
        "July":7, "August":8, "September":9, "October":10, "November":11, "December":12
    }[month]

    cluster_name_map = {
        "🏰 General Disneyland Experience": "General Disneyland Experience",
        "😊 Positive Sentiment & Happiness": "Positive Sentiment & Happiness",
        "🎢 Thrill and Adventure Rides": "Thrill and Adventure Rides",
        "🗺️ Practical Tips and Logistics": "Practical Tips and Logistics",
        "🏨 Hotels and Resort Experience": "Hotels and Resort Experience"
    }
    user_cluster_names = [cluster_name_map[c] for c in clusters] if clusters else list(cluster_name_map.values())

    user_tags = {key: 0 for key in TAG_LABEL_TO_KEY.values()}
    for tag_label in selected_tags:
        key = TAG_LABEL_TO_KEY.get(tag_label)
        if key:
            user_tags[key] = 1

    top_reviews = get_enhanced_similarity(month_number, year, user_cluster_names, user_tags)
    output_str = display_top_similar_reviews(top_reviews)
    return output_str, output_str

# def remove_unicode(text):
#     return text.encode('latin-1', errors='replace').decode('latin-1')

# def save_to_pdf(text):
#     from fpdf import FPDF
#     import tempfile
#     import os

#     class PDF(FPDF):
#         def header(self):
#             self.set_font("Times", style="B", size=16)
#             self.cell(0, 10, "Disneyland Guest Tips", ln=True, align='C')
#             self.ln(10)

#     pdf = PDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)

#     pdf.set_font("Times", size=12)

#     # Remove unsupported unicode chars
#     clean_text = remove_unicode(text)

#     for line in clean_text.split('\n'):
#         pdf.multi_cell(0, 10, line)

#     output_path = os.path.join(tempfile.gettempdir(), "disneyland_guest_tips.pdf")
#     pdf.output(output_path)
#     return output_path
def split_reviews(text):
    # Split by "📅 Visited:" but keep the delimiter using lookahead
    chunks = re.split(r'(?=📅 Visited)', text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def clean_label(text):
    # Remove stars, hashes, dashes, and other leading junk, strip spaces
    text = re.sub(r"^[\*\#\-\s]+", "", text)  # remove leading *, #, -, spaces
    text = re.sub(r"[\*#]", "", text)          # remove any remaining * or #
    text = text.strip()
    text = re.sub(r"\s+", " ", text)           # collapse multiple spaces
    return text

def clean_body(text):
    # Remove stars, hashes, leading/trailing spaces in body text
    text = re.sub(r"[\*\#]", "", text)         # remove stars and hashes anywhere
    text = text.strip()
    # Split into paragraphs by blank lines (one or more newlines)
    paragraphs = re.split(r'\n\s*\n', text)
    cleaned_paragraphs = []
    for p in paragraphs:
        # Clean each paragraph's internal line breaks, collapse spaces
        lines = [line.strip() for line in p.splitlines()]
        paragraph = " ".join(lines)
        cleaned_paragraphs.append(paragraph)
    return cleaned_paragraphs

def save_to_pdf(text):
    pastel_colors = [
        (255, 223, 225), (224, 255, 255), (255, 250, 205), (221, 160, 221),
        (176, 224, 230), (240, 230, 140), (255, 228, 225), (230, 230, 250),
        (255, 239, 213), (152, 251, 152), (176, 196, 222), (240, 255, 240),
        (255, 182, 193), (175, 238, 238), (255, 228, 181), (216, 191, 216),
        (255, 240, 245), (224, 255, 255), (250, 235, 215), (173, 216, 230)
    ]

    reviews = split_reviews(text)
    reviews = reviews[1:]  # Skip the first chunk which is not a review

    class PDF(FPDF):
        def header(self):
            pass

        def footer(self):
            self.set_y(-15)
            self.set_font("DejaVu", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Page {self.page_no()}", align="C")

        def chapter_title(self, num, label, bg_color):
            self.set_fill_color(*bg_color)
            self.set_text_color(70, 70, 70)
            self.set_font("DejaVu", "B", 18)
            self.cell(0, 15, f"Guest {num}", ln=True, fill=True)
            self.ln(5)

        def chapter_body(self, paragraphs):
            self.set_font("DejaVu", size=12)
            self.set_text_color(70, 70, 70)

            for para in paragraphs:
                # Add bullet
                self.write(8, u"\u2022 ")  # Unicode bullet

                # Split paragraph at first colon
                if ':' in para:
                    bold_part, rest = para.split(':', 1)

                    # Write bold part
                    self.set_font("DejaVu", 'B', 16)
                    self.write(8, bold_part + ":")

                    # Write rest of paragraph
                    self.set_font("DejaVu", '', 12)
                    self.write(8, rest.strip())
                else:
                    # No colon, write entire paragraph
                    self.write(8, para)

                # Line break after each paragraph
                self.ln(12)  # spacing between paragraphs

    pdf = PDF()

    # Update font_path with your actual font folder containing DejaVuSans fonts
    font_path = "/Users/lianzou/Desktop/Learning Everything/Disney-itinerary"
    pdf.add_font("DejaVu", "", os.path.join(font_path, "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", "B", os.path.join(font_path, "DejaVuSans-Bold.ttf"), uni=True)
    pdf.add_font("DejaVu", "I", os.path.join(font_path, "DejaVuSans-Oblique.ttf"), uni=True)
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cover Page
    pdf.add_page()
    pdf.set_fill_color(255, 223, 225)
    pdf.rect(0, 0, pdf.w, pdf.h, style="F")
    pdf.set_font("DejaVu", "B", 40)
    pdf.set_text_color(102, 51, 153)
    pdf.ln(50)
    pdf.cell(0, 25, "Disneyland Guest Tips", ln=True, align="C")
    pdf.set_font("DejaVu", "I", 20)
    pdf.set_text_color(120, 120, 120)
    pdf.ln(10)
    pdf.cell(0, 20, "Unlock the magic for your happiest day at Disneyland!", ln=True, align="C")
    pdf.ln(80)
    pdf.set_font("DejaVu", "", 14)
    pdf.cell(0, 10, "Generated with care by Jane Zou", ln=True, align="C")

    # Table of Contents
    pdf.add_page()
    pdf.set_fill_color(224, 255, 255)
    pdf.rect(0, 0, pdf.w, pdf.h, style="F")
    pdf.set_font("DejaVu", "B", 24)
    pdf.set_text_color(102, 102, 102)
    pdf.cell(0, 20, "Table of Contents", ln=True, align="C")
    pdf.ln(10)

    # Prepare cleaned labels for TOC and also keep page numbers
    toc_labels = []
    for i, review in enumerate(reviews, 1):
        # Remove any leading junk from the review itself to avoid repeated "Guest 1"
        clean_review = re.sub(r"^[\-\#\* \n]+", "", review)
        match = re.search(r"^(.*?)(📅 Visited [^\n]*)", clean_review, re.DOTALL)
        label_raw = match.group(1).strip() if match else f"Guest {i}"
        label_clean = clean_label(label_raw)
        if not label_clean:
            label_clean = f"Guest {i}"
        toc_labels.append(label_clean)

    # Reserve pages count for TOC entries to get page numbers right
    # Cover page = 1, TOC page = 2, first review = 3, etc.
    page_start_reviews = 3
    toc_page_number = 2

    pdf.set_font("DejaVu", "", 16)
    # Reserve a list for TOC entries: (label, page number)
    toc_entries = []
    for i, label in enumerate(toc_labels, 1):
        toc_entries.append((f"Guest {i}", page_start_reviews + i - 1))

    # Print TOC entries with dots and page numbers aligned right
    for entry, page_num in toc_entries:
        # Create dots to fill line between label and page number
        line_width = pdf.w - 40  # page width - margins
        # Width of text and page number in points
        text_width = pdf.get_string_width(entry)
        page_width = pdf.get_string_width(str(page_num))
        # Number of dots based on remaining space
        dots_num = int((line_width - (text_width + page_width)) / pdf.get_string_width("."))
        dots = "." * dots_num if dots_num > 0 else " "
        line = f"{entry} {dots} {page_num}"
        pdf.cell(0, 12, line, ln=True)

    # Add reviews pages
    for i, review in enumerate(reviews, 1):
        pdf.add_page()
        bg_color = pastel_colors[(i - 1) % len(pastel_colors)]
        label = toc_labels[i - 1]
        pdf.chapter_title(i, label, bg_color)
        paragraphs = clean_body(review)
        pdf.chapter_body(paragraphs)

    output_path = os.path.join(tempfile.gettempdir(), "disneyland_guest_tips.pdf")
    pdf.output(output_path)
    return output_path

with gr.Blocks(css="""
    body {
        background-color: #fff9fc;
        font-family: "Segoe UI", Tahoma, sans-serif;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
        color: #b469c9;
    }

    .section-subtitle {
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 4px;
        color: #8a4f8b;
    }

    .gr-button {
        background-color: #f9d2e7 !important;
        color: #5e2c68 !important;
        border: none !important;
        font-weight: bold;
        border-radius: 12px !important;
    }

    .gr-button:hover {
        background-color: #f7bfe1 !important;
    }

    .gr-checkbox, .gr-dropdown, .gr-number {
        background-color: #fff0fa !important;
        border: 1px solid #f5cde3 !important;
        border-radius: 10px !important;
    }

    .gr-markdown {
        background-color: #fff5fb;
        border: 1px solid #f2c2e1;
        border-radius: 16px;
        padding: 20px;
        color: #4b3052;
        max-height: 600px;
        overflow-y: auto;
        font-size: 16px;
    }

    label {
        color: #6d3c74 !important;
        font-weight: bold;
    }
""") as demo:

    gr.Markdown("# 🎯 Disneyland Personalized Review Recommender 🎯")
    gr.Markdown("Tell us about your visit and preferences to receive tailored tips from past guests like you!")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown('<div class="section-title">🎟️ Visit Details</div>')
            gr.Markdown('<div class="section-subtitle">When are you visiting?</div>')
            month_input = gr.Dropdown(
                choices=[
                    "January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"
                ],
                label="Month of Visit",
                value="August"
            )
            year_input = gr.Number(
                label="Year of Visit",
                value=2025,
                precision=0,
                minimum=2025,
                maximum=2030,
                step=1
            )

            gr.Markdown('<div class="section-title">🧭 What Do You Want to Focus On?</div>')
            gr.Markdown('<div class="section-subtitle">Pick one or more categories that best match your goals.</div>')
            clusters_input = gr.CheckboxGroup(
                choices=[
                    "🏰 General Disneyland Experience",
                    "😊 Positive Sentiment & Happiness",
                    "🎢 Thrill and Adventure Rides",
                    "🗺️ Practical Tips and Logistics",
                    "🏨 Hotels and Resort Experience"
                ],
                label="",
                value=[]
            )

            gr.Markdown('<div class="section-title">🎯 Personalize Your Experience</div>')
            gr.Markdown('<div class="section-subtitle">Select tags that describe your preferences or needs.</div>')
            gr.Markdown("The more you choose, the more personalized your recommendations will be.")     
            combined_tags_input = gr.CheckboxGroup(
                choices=list(TAG_LABEL_TO_KEY.keys()),
                label="",
                value=[]
            )

            btn = gr.Button("Get Personalized Tips 🎉")

        with gr.Column(scale=2):
            output = gr.Markdown(label="✨ Fellow Guests Help You Build Your Perfect Disneyland Experience ✨")
            file_output = gr.File(label="⬇️ Download These Tips")

    btn.click(
        fn=gradio_review_recommender,
        inputs=[month_input, year_input, clusters_input, combined_tags_input],
        outputs=[output, output]
    ).then(
        fn=save_to_pdf,
        inputs=output,
        outputs=file_output
    )

demo.launch(share=True, debug=True)