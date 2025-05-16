import gradio as gr
from disney_tips import (extract_summary_tfidf, summarize_review_bullets, get_enhanced_similarity)

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
    output_lines.append("### 🌟 Top Tips From Three Guests Most Similar to You 🌟 ###\n")

    for idx, row in top_reviews.iterrows():
        tags = []
        if row.get('tag_has_children'):
            tags.append("👩‍👧 With Kids")
        if row.get('tag_has_teenagers'):
            tags.append("🧑‍🎓 With Teenagers")
        if row.get('tag_needs_guest_services'):
            tags.append("♿ Guest Services Used")
        if row.get('tag_needs_accommodations'):
            tags.append("🧠 Sensory or Special Needs Support")
        if row.get('tag_prefers_quiet'):
            tags.append("🔇 Prefers Calm Spaces")
        if row.get('tag_international_visitor'):
            tags.append("🌍 Visited from Abroad")
        if row.get('tag_special_event_attendee'):
            tags.append("🎉 Attending Special Event")
        if not tags:
            tags.append("👤 General Guest")

        tldr = extract_summary_tfidf(row['Review_Text'], num_sentences=1)
        summary = summarize_review_bullets(row['Review_Text'], num_sentences=3)

        output_lines.append("—" * 100)
        output_lines.append(f"{' | '.join(tags)}  |  📅 Visited: {row['Month_Name']} {row['Year']}")
        output_lines.append(f"📝 TL;DR: {tldr}")
        output_lines.append(summary)
        output_lines.append("")  # blank line between reviews

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
    return display_top_similar_reviews(top_reviews)

with gr.Blocks(css="""
    .section-title {
        font-size: 22px; font-weight: 700; margin-bottom: 8px; color: #3b3b3b;
    }
    .gr-textbox {
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        font-size: 15px;
        white-space: pre-wrap;
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #ddd;
        max-height: 400px;
        overflow-y: auto;
    }
""") as demo:

    gr.Markdown("# 🎯 Disneyland Personalized Review Recommender 🎯")
    gr.Markdown("Select your visit details and preferences to get top guest tips similar to you.")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown('<div class="section-title">Visit Details</div>', elem_classes="section-title")
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
                minimum=2000,
                maximum=2030,
                step=1
            )

            gr.Markdown('<div class="section-title">I Want to Focus On:</div>', elem_classes="section-title")
            clusters_input = gr.CheckboxGroup(
                choices=[
                    "🏰 General Disneyland Experience",
                    "😊 Positive Sentiment & Happiness",
                    "🎢 Thrill and Adventure Rides",
                    "🗺️ Practical Tips and Logistics",
                    "🏨 Hotels and Resort Experience"
                ],
                label="",
                value=["🏰 General Disneyland Experience"]
            )

            gr.Markdown('<div class="section-title">Tag Your Preferences for Better Tips</div>', elem_classes="section-title")
            gr.Markdown("Select all that apply to you. If none, leave blank.")     
            gr.Markdown("**Note:** The more tags you select, the more personalized your recommendations will be.")

            combined_tags_input = gr.CheckboxGroup(
                choices=list(TAG_LABEL_TO_KEY.keys()),
                label="",
                value=[]
            )

        with gr.Column(scale=2):
            output = gr.Textbox(
                label="✨ Fellow Guests Help You Build Your Perfect Disneyland Experience ✨",
                lines=200,
                interactive=False,
                elem_classes="gr-textbox"
            )

    btn = gr.Button("Get Personalized Tips 🎉")
    btn.click(
        fn=gradio_review_recommender,
        inputs=[
            month_input,
            year_input,
            clusters_input,
            combined_tags_input
        ],
        outputs=output
    )

demo.launch()
