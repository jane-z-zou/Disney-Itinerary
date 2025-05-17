# %%
import pandas as pd
import numpy as np
import re
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
file_path = "/Users/lianzou/Desktop/Learning Everything/Disney-itinerary/DisneylandReviews_CA.csv"
df_CA = pd.read_csv(file_path, encoding="ISO-8859-1")

# %%
df_CA = df_CA[df_CA['sentiment'] > 0]

# %%
def circular_month_diff(m1, m2):
    return min(abs(m1 - m2), 12 - abs(m1 - m2))

def clean_and_tokenize(text):
    text = re.sub(r'([.!?])(?!\s)', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return sentences

# %%
def enhanced_similarity(row, user_input, weights):
    month_diff = circular_month_diff(row['Month'], user_input['Month']) / 6
    year_diff = abs(row['Year'] - user_input['Year'])
    cluster_diff = 0 if row['cluster_name'] in user_input['ClusterNames'] else 1
    
    base_similarity = (
        weights['month'] * (1 - month_diff) +
        weights['year'] * (1 - year_diff) +
        weights['cluster'] * (1 - cluster_diff)
    )
    
    # Tags similarity: sum of matches for binary tags
    tags = weights.get('tags', {})
    tag_score = 0
    for tag, weight in tags.items():
        if user_input.get(tag, 0) == 1 and row.get(tag, 0) == 1:
            tag_score += weight

    similarity = base_similarity + tag_score
    return similarity

weights = {
    'month': 0.1,
    'cluster': 0.15,
    'year': 0.05,
    'tags': {
        'tag_has_children': 0.35,
        'tag_has_teenagers': 0.25,
        'tag_needs_guest_services': 0.4,
        'tag_needs_accommodations': 0.4,
        'tag_prefers_quiet': 0.3,
        'tag_international_visitor': 0.2,
        'tag_peak_season_visitor': 0.15,
        'tag_early_or_late_arrival': 0.15,
        'tag_budget_conscious': 0.25,
        'tag_dietary_restrictions': 0.3,
        'tag_foodie_focus': 0.15,
        'tag_thrill_seeker': 0.25,
        'tag_relaxed_rider': 0.25,
        'tag_first_time_visitor': 0.15,
        'tag_frequent_visitor': 0.15,
        'tag_planner': 0.25,
        'tag_go_with_the_flow': 0.15,
        'tag_weather_sensitive': 0.25,
        'tag_needs_rest_breaks': 0.3
    }
}


# %%
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import numpy as np
import textwrap

# Define categories and their keywords
CATEGORY_KEYWORDS = {
    "🎢 Attractions": [
        "ride", "roller coaster", "mountain", "queue", "wait", "line", "fastpass", "genie+", 
        "lightning lane", "standby", "haunted", "pirates", "indiana", "splash", "space mountain", 
        "matterhorn", "jungle cruise", "buzz lightyear", "astro blaster", "small world", 
        "tea cups", "peter pan", "thunder mountain", "radiator springs", "soarin", "incredicoaster", 
        "web slingers", "rise of the resistance", "galaxy's edge"
    ],
    "👧 For Kids": [
        "toddler", "kids", "children", "daughter", "son", "baby", "stroller", "character dining", 
        "bibbidi", "boutique", "meet and greet", "princess", "storybook", "costume", "tea cups", 
        "pixie dust", "play area", "car toon spin", "gadget go coaster", "disney junior"
    ],
    "🍽️ Food": [
        "dining", "restaurant", "snack", "meal", "lunch", "dinner", "breakfast", "mobile order", 
        "blue bayou", "cafe orleans", "churro", "pretzel", "popcorn", "coke", "drink", "treat", 
        "food cart", "resy", "reservation", "dole whip", "tiki juice bar", "galactic grill", 
        "rancho del zocalo", "plaza inn", "corn dog", "mint julep"
    ],
    "📅 Logistics": [
        "reservation", "schedule", "booking", "entry", "check-in", "mobile app", "tip", "plan", 
        "itinerary", "open", "closing", "rope drop", "magic morning", "early entry", "arrival", 
        "navigation", "wait time", "timing", "parade time", "fireworks", "map", "fastpass", 
        "genie", "parking", "tram", "transportation", "security", "bag check"
    ],
    "🧼 Cleanliness": [
        "clean", "dirty", "restroom", "bathroom", "trash", "overflowing", "smell", "sanitary", 
        "cleaning", "janitor", "mess", "filthy", "maintenance", "repair", "broken"
    ],
    "👨‍👩‍👧 Accessibility": [
        "wheelchair", "accessibility", "disability", "accommodation", "mobility", "scooter", 
        "ecv", "guest services", "quiet area", "sensory", "ramp", "hearing", "vision", 
        "allergy", "inclusive", "language support", "translation", "service animal", "support animal"
    ],
    "🎆 Entertainment & Shows": [
        "parade", "show", "fireworks", "light show", "fantasmic", "world of color", "nighttime", 
        "display", "character show", "live", "performer", "music", "projection", "castle show", 
        "soundtrack", "viewing area", "reserved viewing"
    ],
    "🛍️ Shopping & Merchandise": [
        "gift shop", "merchandise", "souvenir", "store", "shop", "ears", "plush", "pins", 
        "collectibles", "lightsaber", "droid", "custom", "shirt", "hat", "apparel", "bubble wand"
    ],
    "🏨 Hotels & Resort Experience": [
        "hotel", "resort", "check-in", "room", "grand californian", "disneyland hotel", 
        "paradise pier", "stay", "bell service", "concierge", "housekeeping", "pool", 
        "view", "parking", "downtown disney", "proximity", "shuttle", "early entry"
    ],
    "🎟️ Pricing & Value": [
        "price", "cost", "expensive", "overpriced", "worth it", "value", "budget", 
        "ticket", "annual pass", "magic key", "day pass", "discount", "deal", "souvenir prices"
    ],
    "😕 Staff & Service": [
        "staff", "cast member", "rude", "helpful", "kind", "unfriendly", "friendly", 
        "customer service", "guest service", "attendant", "employee", "worker", 
        "complaint", "praise", "guide", "direction", "information", "host", "manager"
    ],
    "🌦️ Weather & Environment": [
        "hot", "cold", "rain", "sun", "humid", "shade", "air conditioning", "fans", 
        "umbrella", "jacket", "weather", "temperature", "sunscreen"
    ],
    "📸 Photo Opportunities": [
        "photo", "photopass", "selfie", "picture", "spot", "backdrop", "memory maker", 
        "magic shot", "castle pic", "group photo", "pose"
    ],
    "🧘 Comfort & Energy": [
        "rest", "tired", "break", "relax", "sit", "shade", "bench", "hydrate", 
        "refill station", "rest area", "nap", "slow pace"
    ]
}

# %%
def get_enhanced_similarity(user_month, user_year, user_cluster_names, user_tags=None):
    if user_tags is None:
        user_tags = {}
    
    user_input = {
        'Month': user_month,
        'Year': user_year,
        'ClusterNames': user_cluster_names
    }
    # Add tag preferences to user_input dict with default 0 if not specified
    for tag in weights['tags'].keys():
        user_input[tag] = user_tags.get(tag, 0)

    df_CA['SimilarityScore'] = df_CA.apply(
        lambda row: enhanced_similarity(row, user_input, weights), axis=1
    )

    return df_CA.sort_values(by='SimilarityScore', ascending=False).head(3)

# %%
from collections import defaultdict

def categorize_sentence(sentence, top_k=1):
    lowered = sentence.lower()
    scores = defaultdict(int)

    for category, keywords in CATEGORY_KEYWORDS.items():
        for word in keywords:
            if word in lowered:
                scores[category] += 1

    if not scores:
        return "🔹 Other"

    # Sort categories by match count and return as a single string
    sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_categories = [cat for cat, _ in sorted_categories[:top_k]]
    return ", ".join(top_categories)

def sentiment_icon(sentence):
    polarity = TextBlob(sentence).sentiment.polarity
    if polarity > 0.2:
        return "✅"
    elif polarity < -0.2:
        return "❌"
    else:
        return "⚠️"

# %%
def summarize_review_bullets(text, num_sentences=3, wrap_width=100):
    sentences = clean_and_tokenize(text)
    if len(sentences) <= num_sentences:
        top_sentences = sentences
    else:
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(sentences)
        scores = np.asarray(tfidf_matrix.sum(axis=1)).ravel()
        top_indices = scores.argsort()[-num_sentences:][::-1]
        top_sentences = [sentences[i] for i in sorted(top_indices)]

    # Categorize and add sentiment icons
    bullets = []
    for sent in top_sentences:
        category = categorize_sentence(sent)
        icon = sentiment_icon(sent)
        wrapped = textwrap.fill(f"{icon} {sent}", width=wrap_width)
        bullets.append((category, wrapped))

    # Group by category
    grouped = defaultdict(list)
    for category, bullet in bullets:
        grouped[category].append(bullet)

    # Print grouped output
    output = ""
    for cat, lines in grouped.items():
        output += f"\n{cat}:\n"
        for line in lines:
            output += f"{line}\n"
    return output

# %%
def extract_summary_tfidf(text, num_sentences=1):
    sentences = clean_and_tokenize(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    sentence_scores = np.asarray(tfidf_matrix.sum(axis=1)).ravel()

    top_indices = sentence_scores.argsort()[-num_sentences:][::-1]
    top_sentences = [sentences[i] for i in sorted(top_indices)]

    return " ".join(top_sentences)

# %%
# Simulated user checkbox inputs (1 = checked, 0 = unchecked)
user_tags = {
    'tag_has_children': 0,
    'tag_has_teenagers': 0,
    'tag_needs_guest_services': 0,
    'tag_needs_accommodations': 0,
    'tag_prefers_quiet': 1,
    'tag_international_visitor': 0,
    'tag_peak_season_visitor': 1,
    'tag_early_or_late_arrival': 0,
    'tag_budget_conscious': 1,
    'tag_dietary_restrictions': 0,
    'tag_foodie_focus': 1,
    'tag_thrill_seeker': 1,
    'tag_relaxed_rider': 1,
    'tag_first_time_visitor': 0,
    'tag_frequent_visitor': 0,
    'tag_special_event_attendee': 1,
    'tag_planner': 1,
    'tag_go_with_the_flow': 0,
    'tag_weather_sensitive': 1,
    'tag_needs_rest_breaks': 1
}

user_month = 12  # December
user_year = 2025
user_cluster_names = ["General Disneyland Experience", "Positive Sentiment & Happiness"]

# Call your enhanced similarity function passing the explicit user tags
top_reviews = get_enhanced_similarity(user_month, user_year, user_cluster_names, user_tags)
print("### 🌟 Top Tips From Three Guests Most Similar to You 🌟 ###")
    
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
        tags.append("🎉 Attended Special Event")
    if not tags:
        tags.append("👤 General Guest")
    
    tldr = extract_summary_tfidf(row['Review_Text'], num_sentences=1)
    summary = summarize_review_bullets(row['Review_Text'], num_sentences=3)
    
    print("—" * 100)
    print(f"{' | '.join(tags)}  |  📅 Visited: {row['Month_Name']} {row['Year']}")
    print("📝 TL;DR:", tldr)
    print(summary)


