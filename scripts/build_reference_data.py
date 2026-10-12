#!/usr/bin/env python3
# Build reference datasets: normalize raw sources in dataset/ into data/ JSON.

import os
import json
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATASET_DIR = ROOT_DIR / "dataset"
FRONTEND_PUBLIC_CARDS = ROOT_DIR / "frontend" / "public" / "cards"


def build_tarot_deck():
    print("[1/5] Building data/tarot/rider_waite_deck.json and syncing card imagery...")
    tarot_dir = DATA_DIR / "tarot"
    tarot_dir.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC_CARDS.mkdir(parents=True, exist_ok=True)

    meanings_file = DATASET_DIR / "Toroto card" / "tarot meaning" / "cards.json"
    images_file = DATASET_DIR / "Toroto card" / "Tarot Deck" / "tarot-images.json"
    cards_source_dir = DATASET_DIR / "Toroto card" / "Tarot Deck" / "cards"

    with open(meanings_file, "r", encoding="utf-8") as f:
        meanings_list = json.load(f)

    with open(images_file, "r", encoding="utf-8") as f:
        images_data = json.load(f)

    img_map = {c["name"].strip().lower(): c for c in images_data["cards"]}

    normalized_cards = []
    copied_images = 0

    for item in meanings_list:
        name = item["name"].strip()
        key = name.lower()
        img_info = img_map.get(key, {})
        img_filename = img_info.get("img", "")

        arcana = item.get("arcana", "").lower()
        suit = item.get("suit")
        suit_str = suit.lower() if suit else None
        num = item.get("number_numerology")
        if num is None:
            num = item.get("id", 0)

        slug_name = name.lower().replace(" ", "-").replace("'", "")
        if arcana == "major":
            card_id = f"major-{num:02d}-{slug_name}"
        else:
            card_id = f"minor-{suit_str}-{num:02d}-{slug_name}"

        # Copy image file to frontend/public/cards
        src_img = cards_source_dir / img_filename
        dst_img = FRONTEND_PUBLIC_CARDS / img_filename
        if src_img.exists():
            if not dst_img.exists() or dst_img.stat().st_size != src_img.stat().st_size:
                shutil.copy2(src_img, dst_img)
            copied_images += 1

        kw_upright = item.get("keywords_upright", [])
        kw_reversed = item.get("keywords_reversed", [])
        general_keywords = img_info.get("keywords", [])
        combined_keywords = list(dict.fromkeys(kw_upright + general_keywords))

        card_obj = {
            "id": card_id,
            "name": name,
            "number": num,
            "arcana": arcana,
            "suit": suit_str,
            "element": item.get("element"),
            "planet": item.get("planet"),
            "zodiac": item.get("zodiac"),
            "yes_no": item.get("yes_no"),
            "yes_no_reversed": item.get("yes_no_reversed"),
            "keywords": combined_keywords,
            "keywords_upright": kw_upright,
            "keywords_reversed": kw_reversed,
            "upright_meaning": item.get("meaning_upright", ""),
            "reversed_meaning": item.get("meaning_reversed", ""),
            "fortune_telling": img_info.get("fortune_telling", []),
            "meanings_light": img_info.get("meanings", {}).get("light", []),
            "meanings_shadow": img_info.get("meanings", {}).get("shadow", []),
            "domains": {
                "love": item.get("love", ""),
                "love_reversed": item.get("love_reversed", ""),
                "career": item.get("career", ""),
                "career_reversed": item.get("career_reversed", ""),
                "mood": item.get("mood", ""),
                "mood_reversed": item.get("mood_reversed", ""),
                "spiritual": item.get("spiritual", ""),
                "spiritual_reversed": item.get("spiritual_reversed", "")
            },
            "image_file": img_filename,
            "image_path": f"/cards/{img_filename}"
        }
        normalized_cards.append(card_obj)

    deck_output = {
        "deck_id": "rider_waite_smith",
        "name": "Rider-Waite-Smith Tarot Deck",
        "author": "Arthur Edward Waite & Pamela Colman Smith (1909)",
        "description": "Standard 78-card Rider-Waite-Smith tarot deck including 22 Major Arcana and 56 Minor Arcana cards across Wands, Cups, Swords, and Pentacles.",
        "total_cards": len(normalized_cards),
        "major_arcana_count": sum(1 for c in normalized_cards if c["arcana"] == "major"),
        "minor_arcana_count": sum(1 for c in normalized_cards if c["arcana"] == "minor"),
        "suits": ["wands", "cups", "swords", "pentacles"],
        "cards": normalized_cards
    }

    out_file = tarot_dir / "rider_waite_deck.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(deck_output, f, indent=2, ensure_ascii=False)

    print(f"  -> Successfully generated {out_file.name} ({len(normalized_cards)} cards, {copied_images} images synced).")


def build_tarot_spreads():
    print("[2/5] Building data/tarot/spreads.json...")
    spreads_data = {
        "version": "1.0.0",
        "description": "Standardized tarot spreads defined for the Palmistry & Tarot Intelligence Platform (Spec §49.6, FR-017..FR-022).",
        "spreads": [
            {
                "id": "single_card",
                "name": "Single Card Spread",
                "spec_requirement": "FR-017",
                "card_count": 1,
                "category": "daily_focus",
                "description": "A single-card draw providing direct spiritual guidance, daily focus, or a clear answer to a focused inquiry.",
                "positions": [
                    {
                        "position": 1,
                        "name": "Core Guidance",
                        "description": "The primary energy, theme, or lesson currently governing your inquiry.",
                        "layout_coordinate": {"x": 0.5, "y": 0.5}
                    }
                ],
                "interpretation_order": [1]
            },
            {
                "id": "three_card",
                "name": "Three Card Spread (Past, Present, Future)",
                "spec_requirement": "FR-018",
                "card_count": 3,
                "category": "temporal_overview",
                "description": "The classic three-card spread tracing chronological momentum from roots through current experience to emerging trajectory.",
                "positions": [
                    {
                        "position": 1,
                        "name": "The Past",
                        "description": "Foundations, root causes, past lessons, and background energies shaping the present.",
                        "layout_coordinate": {"x": 0.2, "y": 0.5}
                    },
                    {
                        "position": 2,
                        "name": "The Present",
                        "description": "Current reality, active dynamics, immediate challenges, and where your focus is centered.",
                        "layout_coordinate": {"x": 0.5, "y": 0.5}
                    },
                    {
                        "position": 3,
                        "name": "The Future",
                        "description": "Emerging trajectory, potential outcome, and advice for navigating what lies ahead.",
                        "layout_coordinate": {"x": 0.8, "y": 0.5}
                    }
                ],
                "interpretation_order": [1, 2, 3]
            },
            {
                "id": "relationship",
                "name": "Relationship Harmony Spread",
                "spec_requirement": "FR-019",
                "card_count": 5,
                "category": "interpersonal",
                "description": "A 5-card diagnostic examining personal perspectives, interpersonal bonds, hidden blocks, and mutual growth pathways.",
                "positions": [
                    {
                        "position": 1,
                        "name": "Querent / Your Perspective",
                        "description": "Your emotional state, expectations, and energy brought into the connection.",
                        "layout_coordinate": {"x": 0.2, "y": 0.6}
                    },
                    {
                        "position": 2,
                        "name": "Partner / Other's Perspective",
                        "description": "Their viewpoint, underlying feelings, and current attitude toward the connection.",
                        "layout_coordinate": {"x": 0.8, "y": 0.6}
                    },
                    {
                        "position": 3,
                        "name": "The Dynamic / Connection",
                        "description": "The core energy and nature of the bond uniting the two parties.",
                        "layout_coordinate": {"x": 0.5, "y": 0.4}
                    },
                    {
                        "position": 4,
                        "name": "Hidden Influences / Obstacle",
                        "description": "Unspoken tensions, external pressures, or blind spots requiring illumination.",
                        "layout_coordinate": {"x": 0.5, "y": 0.7}
                    },
                    {
                        "position": 5,
                        "name": "Resolution / Path Forward",
                        "description": "The potential outcome and constructive guidance for mutual elevation.",
                        "layout_coordinate": {"x": 0.5, "y": 0.15}
                    }
                ],
                "interpretation_order": [1, 2, 3, 4, 5]
            },
            {
                "id": "career",
                "name": "Career & Ambition Spread",
                "spec_requirement": "FR-020",
                "card_count": 5,
                "category": "professional",
                "description": "A 5-card strategic layout evaluating current career standing, ambitions, hidden workplace dynamics, and professional milestones.",
                "positions": [
                    {
                        "position": 1,
                        "name": "Current Career Standing",
                        "description": "Where you currently stand in your professional trajectory and workspace.",
                        "layout_coordinate": {"x": 0.5, "y": 0.75}
                    },
                    {
                        "position": 2,
                        "name": "True Aspirations & Calling",
                        "description": "Your authentic ambition, creative desires, and ultimate career goals.",
                        "layout_coordinate": {"x": 0.5, "y": 0.45}
                    },
                    {
                        "position": 3,
                        "name": "Challenges & Workplace Blocks",
                        "description": "Obstacles, competition, internal self-doubt, or organizational friction.",
                        "layout_coordinate": {"x": 0.2, "y": 0.45}
                    },
                    {
                        "position": 4,
                        "name": "Actionable Strategy",
                        "description": "The tactical step, skill to hone, or decision to execute now.",
                        "layout_coordinate": {"x": 0.8, "y": 0.45}
                    },
                    {
                        "position": 5,
                        "name": "Professional Milestone / Outcome",
                        "description": "The long-term realization and career success awaiting dedication.",
                        "layout_coordinate": {"x": 0.5, "y": 0.15}
                    }
                ],
                "interpretation_order": [1, 2, 3, 4, 5]
            },
            {
                "id": "celtic_cross",
                "name": "The Celtic Cross Spread",
                "spec_requirement": "FR-021",
                "card_count": 10,
                "category": "comprehensive_destiny",
                "description": "The time-honored 10-card master spread dissecting intricate life situations across conscious aims, subconscious drives, past roots, and future convergence.",
                "positions": [
                    {
                        "position": 1,
                        "name": "The Present / Heart of the Matter",
                        "description": "The core situation, query, and central atmosphere enveloping the querent.",
                        "layout_coordinate": {"x": 0.35, "y": 0.5}
                    },
                    {
                        "position": 2,
                        "name": "The Challenge / Crossing Card",
                        "description": "The immediate obstacle, friction, or catalyst crossing the present energy.",
                        "layout_coordinate": {"x": 0.35, "y": 0.5, "cross": True}
                    },
                    {
                        "position": 3,
                        "name": "The Past / Deep Foundation",
                        "description": "The underlying roots, past choices, and foundational events giving rise to today.",
                        "layout_coordinate": {"x": 0.35, "y": 0.8}
                    },
                    {
                        "position": 4,
                        "name": "Passing Influences / Recent Past",
                        "description": "Energies or circumstances that are receding and fading out of relevance.",
                        "layout_coordinate": {"x": 0.15, "y": 0.5}
                    },
                    {
                        "position": 5,
                        "name": "Conscious Goal / The Crown",
                        "description": "What you consciously aspire toward and the highest attainable ideal in this scenario.",
                        "layout_coordinate": {"x": 0.35, "y": 0.2}
                    },
                    {
                        "position": 6,
                        "name": "Immediate Horizon / Near Future",
                        "description": "Upcoming events and shifts arriving in the immediate future.",
                        "layout_coordinate": {"x": 0.55, "y": 0.5}
                    },
                    {
                        "position": 7,
                        "name": "The Querent / Internal Mindset",
                        "description": "Your internal perspective, emotional posture, and how you perceive yourself in this moment.",
                        "layout_coordinate": {"x": 0.85, "y": 0.85}
                    },
                    {
                        "position": 8,
                        "name": "External Influences & Environment",
                        "description": "The social circle, family, friends, workplace context, and external environment.",
                        "layout_coordinate": {"x": 0.85, "y": 0.62}
                    },
                    {
                        "position": 9,
                        "name": "Hopes & Secret Fears",
                        "description": "Your deepest psychological hopes and the corresponding subconscious anxieties.",
                        "layout_coordinate": {"x": 0.85, "y": 0.38}
                    },
                    {
                        "position": 10,
                        "name": "Ultimate Outcome / Culmination",
                        "description": "The synthesized culmination of energies and the ultimate long-term trajectory.",
                        "layout_coordinate": {"x": 0.85, "y": 0.15}
                    }
                ],
                "interpretation_order": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            },
            {
                "id": "life_path",
                "name": "Life Path & Soul Purpose Spread",
                "spec_requirement": "FR-022",
                "card_count": 7,
                "category": "spiritual_evolution",
                "description": "A 7-card esoteric layout illuminating the querent's spiritual essence, karmic challenges, innate blessings, and highest personal potential.",
                "positions": [
                    {
                        "position": 1,
                        "name": "Core Soul Identity",
                        "description": "Your authentic spiritual frequency and true higher-self essence.",
                        "layout_coordinate": {"x": 0.5, "y": 0.85}
                    },
                    {
                        "position": 2,
                        "name": "Current Incarnate Path",
                        "description": "The earthly journey and lesson path you are actively traversing.",
                        "layout_coordinate": {"x": 0.3, "y": 0.65}
                    },
                    {
                        "position": 3,
                        "name": "Karmic Lesson",
                        "description": "The recurring life lesson and spiritual debt to be integrated with grace.",
                        "layout_coordinate": {"x": 0.7, "y": 0.65}
                    },
                    {
                        "position": 4,
                        "name": "Innate Gifts & Blessings",
                        "description": "Your natural talents, psychic gifts, and intuitive strengths.",
                        "layout_coordinate": {"x": 0.2, "y": 0.45}
                    },
                    {
                        "position": 5,
                        "name": "Subconscious Shadow & Potential",
                        "description": "Unawakened powers and hidden dimensions waiting to be integrated into consciousness.",
                        "layout_coordinate": {"x": 0.8, "y": 0.45}
                    },
                    {
                        "position": 6,
                        "name": "The Next Spiritual Horizon",
                        "description": "The gateway and transformative shift opening in your life journey.",
                        "layout_coordinate": {"x": 0.5, "y": 0.35}
                    },
                    {
                        "position": 7,
                        "name": "Ultimate Spiritual Destiny",
                        "description": "The highest realization of your purpose and personal enlightenment in this lifetime.",
                        "layout_coordinate": {"x": 0.5, "y": 0.12}
                    }
                ],
                "interpretation_order": [1, 2, 3, 4, 5, 6, 7]
            }
        ]
    }

    out_file = DATA_DIR / "tarot" / "spreads.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(spreads_data, f, indent=2, ensure_ascii=False)

    print(f"  -> Successfully generated {out_file.name} (6 spreads).")


def build_palm_lines_catalog():
    print("[3/5] Building data/palmistry/lines_catalog.json...")
    palm_dir = DATA_DIR / "palmistry"
    palm_dir.mkdir(parents=True, exist_ok=True)

    lines_data = {
        "version": "1.0.0",
        "description": "Primary palm lines catalog for the Palmistry & Tarot Intelligence Platform (Spec §49.5, FR-009).",
        "required_lines_count": 5,
        "lines": [
            {
                "id": "life_line",
                "name": "Life Line",
                "classical_name": "Linea Vitae",
                "sanskrit_name": "Pitri Rekha (Vitality Line)",
                "category": "major_line",
                "description": "Curves around the base of the thumb (Mount of Venus); represents vitality, physical energy, health stamina, and significant life transitions.",
                "significance": [
                    "physical vitality and stamina",
                    "general health constitution",
                    "major life transitions and geographic relocations",
                    "quality of life energy and enthusiasm"
                ],
                "starting_zone": "Radial edge of the palm between the index finger (Jupiter) and thumb (Venus).",
                "ending_zone": "Base of the palm near the wrist (Rascettes) curving around Mount of Venus.",
                "variations": [
                    {
                        "type": "long_and_deep",
                        "description": "Long, clear, and well-defined line curving gracefully around the thumb.",
                        "meaning": "Vibrant vitality, strong constitution, steady stamina, and grounded physical presence."
                    },
                    {
                        "type": "faint_or_shallow",
                        "description": "Thin, superficial line requiring close inspection to trace.",
                        "meaning": "Sensitive constitution, needing deliberate rest, prone to nervous energy exhaustion."
                    },
                    {
                        "type": "wide_arc",
                        "description": "Sweeps broadly toward the center of the palm before descending.",
                        "meaning": "Expansive enthusiasm, generous warm heart, love of adventure and travel."
                    },
                    {
                        "type": "close_to_thumb",
                        "description": "Stays tightly enclosed against the ball of the thumb.",
                        "meaning": "Cautious nature, introverted reserve, conservative with energy and resources."
                    },
                    {
                        "type": "forked_at_base",
                        "description": "Branching into two or more strands as it reaches the wrist.",
                        "meaning": "Travel abroad, profound life shift in maturity, dual residences or pursuits."
                    }
                ],
                "confidence_threshold_default": 0.65
            },
            {
                "id": "head_line",
                "name": "Head Line",
                "classical_name": "Linea Capitis",
                "sanskrit_name": "Matri Rekha (Wisdom Line)",
                "category": "major_line",
                "description": "Traverses horizontally across the palm between the Life and Heart lines; governs cognitive style, intellect, reasoning focus, and mental processing.",
                "significance": [
                    "intellectual orientation (analytical vs creative)",
                    "mental focus, concentration, and clarity",
                    "decision-making style and risk tolerance",
                    "communication and psychological adaptability"
                ],
                "starting_zone": "Originates near or joined with the Life Line above the Mount of Venus.",
                "ending_zone": "Crosses the palm toward the Mount of Mars (percussive edge) or slants down toward the Mount of Moon.",
                "variations": [
                    {
                        "type": "straight_and_horizontal",
                        "description": "Extends directly across the palm toward the upper percussion (Mount of Mars).",
                        "meaning": "Highly practical, logical, data-driven, objective problem solver with disciplined focus."
                    },
                    {
                        "type": "sloping_toward_moon",
                        "description": "Curving gently downward toward the fleshy base of the Mount of Moon.",
                        "meaning": "Rich creative imagination, artistic sensitivity, intuitive cognition, literary flair."
                    },
                    {
                        "type": "writers_fork",
                        "description": "Splits into a distinct fork near the termination (one branch straight, one dipping to Moon).",
                        "meaning": "The Writer's Fork: rare blend of analytical pragmatism and brilliant creative imagination."
                    },
                    {
                        "type": "joined_with_life_line",
                        "description": "Originates entwined with the Life Line for a centimeter or more.",
                        "meaning": "Deeply reflective, cautious start in youth, values family counsel, considerate."
                    },
                    {
                        "type": "separated_from_life_line",
                        "description": "Clear gap between the start of the Head Line and Life Line.",
                        "meaning": "Independent thinker, pioneering spirit, bold self-confidence, takes initiative early."
                    }
                ],
                "confidence_threshold_default": 0.65
            },
            {
                "id": "heart_line",
                "name": "Heart Line",
                "classical_name": "Linea Mensalis",
                "sanskrit_name": "Ayush Rekha (Emotion Line)",
                "category": "major_line",
                "description": "Runs across the upper palm below the fingers; governs emotional depth, romantic style, empathy, compassion, and interpersonal vulnerability.",
                "significance": [
                    "emotional expression and vulnerability",
                    "romantic ideals, loyalty, and relationship patterns",
                    "empathy, social compassion, and emotional boundaries",
                    "cardiovascular and emotional equilibrium"
                ],
                "starting_zone": "Ulnar percussion of the hand below the little finger (Mercury).",
                "ending_zone": "Sweeps across the upper palm toward the Mount of Jupiter (index) or Mount of Saturn (middle).",
                "variations": [
                    {
                        "type": "curved_to_jupiter",
                        "description": "Curving upward and terminating gracefully under the index finger (Mount of Jupiter).",
                        "meaning": "Idealistic in love, affectionate, noble expectations, warm-hearted, deeply loyal partner."
                    },
                    {
                        "type": "straight_and_terminating_at_saturn",
                        "description": "Flat, straight trajectory terminating beneath the middle finger (Mount of Saturn).",
                        "meaning": "Realistic, emotionally guarded, values stability and demonstrated action over romantic idealism."
                    },
                    {
                        "type": "ending_between_jupiter_and_saturn",
                        "description": "Balanced termination right in the valley between the index and middle fingers.",
                        "meaning": "Golden emotional balance: gives love warmly while maintaining healthy self-respect and boundaries."
                    },
                    {
                        "type": "chained_or_feathered",
                        "description": "Small island links or feathery branches along the line.",
                        "meaning": "High emotional sensitivity, deeply empathetic, absorbs energy of surroundings easily."
                    }
                ],
                "confidence_threshold_default": 0.65
            },
            {
                "id": "fate_line",
                "name": "Fate Line",
                "classical_name": "Linea Saturni (Destiny Line)",
                "sanskrit_name": "Bhagya Rekha",
                "category": "major_line",
                "description": "Ascends vertically up the center of the palm toward the middle finger (Mount of Saturn); reflects vocation, sense of purpose, life direction, and external karmic tides.",
                "significance": [
                    "career path clarity and professional dedication",
                    "sense of purpose and vocational direction",
                    "self-determined vs externally influenced destiny",
                    "pivotal career shifts and vocational transitions"
                ],
                "starting_zone": "Base of palm near the wrist, or rising from the Life Line or Mount of Moon.",
                "ending_zone": "Mount of Saturn (below middle finger).",
                "variations": [
                    {
                        "type": "deep_and_straight",
                        "description": "Continuous, unbroken vertical column from wrist to Saturn mount.",
                        "meaning": "Unshakable vocational clarity from an early age, self-directed achievement, high career focus."
                    },
                    {
                        "type": "rising_from_moon",
                        "description": "Originates from the fleshy Mount of Moon (outer palm edge).",
                        "meaning": "Career dependent on public rapport, client charisma, artistic recognition, or support of others."
                    },
                    {
                        "type": "rising_from_life_line",
                        "description": "Sprouts from the Life Line further up the hand.",
                        "meaning": "Self-made success: career breakthroughs won through personal grit and dedicated perseverance."
                    },
                    {
                        "type": "faint_or_absent",
                        "description": "Faint, intermittent, or absent.",
                        "meaning": "Flexible, self-authored journey: free from rigid corporate ladders, crafting varied eclectic paths."
                    }
                ],
                "confidence_threshold_default": 0.55
            },
            {
                "id": "sun_line",
                "name": "Sun Line",
                "classical_name": "Linea Solaris (Apollo Line)",
                "sanskrit_name": "Surya Rekha (Success & Brilliance Line)",
                "category": "major_line",
                "description": "Runs vertically parallel to the Fate Line toward the ring finger (Mount of Apollo); signifies public recognition, charisma, artistic fulfillment, and personal magnetism.",
                "significance": [
                    "public acclaim, fame, and reputation",
                    "artistic talent, aesthetic refinement, and creative genius",
                    "charismatic presence and social warmth",
                    "reward and recognition fulfilling career labor"
                ],
                "starting_zone": "Lower palm, or ascending from Heart Line, Head Line, or Fate Line.",
                "ending_zone": "Mount of Apollo (base of the ring finger).",
                "variations": [
                    {
                        "type": "strong_and_unbroken",
                        "description": "Clear vertical line reaching onto the Apollo mount.",
                        "meaning": "Profound artistic brilliance, high public visibility, magnetic charisma, acknowledged success."
                    },
                    {
                        "type": "rising_from_heart_line",
                        "description": "Begins only above the Heart Line and ascends into Apollo.",
                        "meaning": "Late-blooming brilliance: public recognition, joy, and greatest success achieved in mature years."
                    },
                    {
                        "type": "multiple_parallel_lines",
                        "description": "Two or three slender parallel lines ascending under ring finger.",
                        "meaning": "Versatile creative interests, multiple concurrent artistic pursuits, widely appreciated."
                    },
                    {
                        "type": "absent",
                        "description": "Not visibly delineated on palm surface.",
                        "meaning": "Quiet fulfillment: success achieved through steadfast internal satisfaction rather than celebrity or fame."
                    }
                ],
                "confidence_threshold_default": 0.50
            }
        ]
    }

    out_file = palm_dir / "lines_catalog.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(lines_data, f, indent=2, ensure_ascii=False)

    print(f"  -> Successfully generated {out_file.name} (5 lines).")


def build_palm_mounts_catalog():
    print("[4/5] Building data/palmistry/mounts_catalog.json...")
    palm_dir = DATA_DIR / "palmistry"
    palm_dir.mkdir(parents=True, exist_ok=True)

    mounts_data = {
        "version": "1.0.0",
        "description": "Traditional palm mounts catalog with MediaPipe anatomical anchors (Spec §49.5, FR-011).",
        "mounts": [
            {
                "id": "mount_of_jupiter",
                "name": "Mount of Jupiter",
                "planetary_ruler": "Jupiter",
                "element": "Fire",
                "anatomical_anchor": {
                    "mediapipe_index": 5,
                    "landmark_name": "INDEX_FINGER_MCP",
                    "region": "Directly below the index finger base on upper radial palm."
                },
                "core_attributes": ["leadership", "ambition", "confidence", "honor", "wisdom"],
                "prominence_meanings": {
                    "underdeveloped": "Humility, diffidence, self-effacing, prefers supportive or background roles.",
                    "balanced": "Natural dignity, confident leadership, visionary ambition, balanced self-esteem.",
                    "prominent": "Dominant personality, proud, natural commander, strongly ambitious and competitive."
                }
            },
            {
                "id": "mount_of_saturn",
                "name": "Mount of Saturn",
                "planetary_ruler": "Saturn",
                "element": "Earth",
                "anatomical_anchor": {
                    "mediapipe_index": 9,
                    "landmark_name": "MIDDLE_FINGER_MCP",
                    "region": "Directly beneath the middle finger base."
                },
                "core_attributes": ["discipline", "responsibility", "prudence", "introspection", "wisdom"],
                "prominence_meanings": {
                    "underdeveloped": "Lighthearted, carefree, dislikes solitary work, lives for the moment.",
                    "balanced": "Philosophical, disciplined, responsible, ethical, deep thinker with quiet endurance.",
                    "prominent": "Serious, introverted, solitary temperament, intensely studious, highly cautious."
                }
            },
            {
                "id": "mount_of_apollo",
                "name": "Mount of Apollo (Sun Mount)",
                "planetary_ruler": "Sun",
                "element": "Fire",
                "anatomical_anchor": {
                    "mediapipe_index": 13,
                    "landmark_name": "RING_FINGER_MCP",
                    "region": "Directly below the ring finger base."
                },
                "core_attributes": ["creativity", "artistic talent", "joy", "charm", "aesthetic appreciation"],
                "prominence_meanings": {
                    "underdeveloped": "Utilitarian mindset, indifferent to arts or aesthetics, grounded in practical necessities.",
                    "balanced": "Refined artistic taste, radiant warmth, optimistic spirit, magnetic social grace.",
                    "prominent": "Extravagant love of beauty, dramatic flair, craving for applause and celebrity spotlight."
                }
            },
            {
                "id": "mount_of_mercury",
                "name": "Mount of Mercury",
                "planetary_ruler": "Mercury",
                "element": "Air",
                "anatomical_anchor": {
                    "mediapipe_index": 17,
                    "landmark_name": "PINKY_MCP",
                    "region": "Directly beneath the little finger base."
                },
                "core_attributes": ["communication", "wit", "adaptability", "business acumen", "intellect"],
                "prominence_meanings": {
                    "underdeveloped": "Shy in speech, straightforward, prefers simple conversations over negotiation.",
                    "balanced": "Persuasive speaker, sharp intellect, commercial savvy, swift adaptability.",
                    "prominent": "Exceptionally articulate, fast-talking, sharp negotiator, inventive mind."
                }
            },
            {
                "id": "mount_of_venus",
                "name": "Mount of Venus",
                "planetary_ruler": "Venus",
                "element": "Water / Earth",
                "anatomical_anchor": {
                    "mediapipe_index": 1,
                    "landmark_name": "THUMB_CMC",
                    "region": "The fleshy ball of the palm enclosed by the Life Line."
                },
                "core_attributes": ["vitality", "sensuality", "love", "passion", "generosity"],
                "prominence_meanings": {
                    "underdeveloped": "Ascetic nature, detached from sensual pleasures, reserved in physical affections.",
                    "balanced": "Warm-hearted, passionate, vibrant vitality, loving, appreciative of music and beauty.",
                    "prominent": "Deeply passionate, hedonistic love of pleasure, abundant physical energy."
                }
            },
            {
                "id": "mount_of_moon",
                "name": "Mount of Moon (Mount of Luna)",
                "planetary_ruler": "Moon",
                "element": "Water",
                "anatomical_anchor": {
                    "mediapipe_index": 0,
                    "landmark_name": "WRIST",
                    "region": "The fleshy lower percussion on the outer edge of the palm opposite the thumb."
                },
                "core_attributes": ["intuition", "imagination", "dreams", "mysticism", "empathy"],
                "prominence_meanings": {
                    "underdeveloped": "Hyper-realistic, grounded strictly in tangible facts, rare daydreams.",
                    "balanced": "Intuitive insight, vivid imagination, empathetic emotional antenna, artistic flair.",
                    "prominent": "Visionary dreamer, profound mystical sensibilities, poetic, highly receptive to psychic impressions."
                }
            }
        ]
    }

    out_file = palm_dir / "mounts_catalog.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mounts_data, f, indent=2, ensure_ascii=False)

    print(f"  -> Successfully generated {out_file.name} (6 mounts).")


def build_hand_landmarks_schema():
    print("[5/5] Building data/landmarks/hand_landmarks_schema.json...")
    landmarks_dir = DATA_DIR / "landmarks"
    landmarks_dir.mkdir(parents=True, exist_ok=True)

    landmarks_schema = {
        "version": "1.0.0",
        "description": "MediaPipe Hand Landmarker 21-point topology reference mapping for palmistry geometry (Spec §49.5).",
        "total_landmarks": 21,
        "landmarks": [
            {"index": 0, "name": "WRIST", "category": "wrist", "palmistry_role": "Rascettes / Bracelets origin, Moon-Venus baseline."},
            {"index": 1, "name": "THUMB_CMC", "category": "thumb", "palmistry_role": "Mount of Venus base anchor."},
            {"index": 2, "name": "THUMB_MCP", "category": "thumb", "palmistry_role": "Mount of Venus upper border, Life Line origin zone."},
            {"index": 3, "name": "THUMB_IP", "category": "thumb", "palmistry_role": "Willpower phalanx of the thumb."},
            {"index": 4, "name": "THUMB_TIP", "category": "thumb", "palmistry_role": "Logic/Intuition apex of the thumb."},
            {"index": 5, "name": "INDEX_FINGER_MCP", "category": "index", "palmistry_role": "Mount of Jupiter center anchor; Head Line origin calibration."},
            {"index": 6, "name": "INDEX_FINGER_PIP", "category": "index", "palmistry_role": "Ambition phalanx."},
            {"index": 7, "name": "INDEX_FINGER_DIP", "category": "index", "palmistry_role": "Philosophy phalanx."},
            {"index": 8, "name": "INDEX_FINGER_TIP", "category": "index", "palmistry_role": "Executive index apex."},
            {"index": 9, "name": "MIDDLE_FINGER_MCP", "category": "middle", "palmistry_role": "Mount of Saturn center anchor; Fate Line termination target."},
            {"index": 10, "name": "MIDDLE_FINGER_PIP", "category": "middle", "palmistry_role": "Duty phalanx."},
            {"index": 11, "name": "MIDDLE_FINGER_DIP", "category": "middle", "palmistry_role": "Sobriety phalanx."},
            {"index": 12, "name": "MIDDLE_FINGER_TIP", "category": "middle", "palmistry_role": "Saturnian discipline apex."},
            {"index": 13, "name": "RING_FINGER_MCP", "category": "ring", "palmistry_role": "Mount of Apollo center anchor; Sun Line termination target."},
            {"index": 14, "name": "RING_FINGER_PIP", "category": "ring", "palmistry_role": "Aesthetic phalanx."},
            {"index": 15, "name": "RING_FINGER_DIP", "category": "ring", "palmistry_role": "Artistic discernment phalanx."},
            {"index": 16, "name": "RING_FINGER_TIP", "category": "ring", "palmistry_role": "Solar creative apex."},
            {"index": 17, "name": "PINKY_MCP", "category": "pinky", "palmistry_role": "Mount of Mercury center anchor; Heart Line origin calibration."},
            {"index": 18, "name": "PINKY_PIP", "category": "pinky", "palmistry_role": "Commerce/Negotiation phalanx."},
            {"index": 19, "name": "PINKY_DIP", "category": "pinky", "palmistry_role": "Tact phalanx."},
            {"index": 20, "name": "PINKY_TIP", "category": "pinky", "palmistry_role": "Mercurial eloquence apex."}
        ],
        "connections": [
            [0, 1], [1, 2], [2, 3], [3, 4],
            [0, 5], [5, 6], [6, 7], [7, 8],
            [5, 9], [9, 10], [10, 11], [11, 12],
            [9, 13], [13, 14], [14, 15], [15, 16],
            [13, 17], [17, 18], [18, 19], [19, 20],
            [0, 17]
        ],
        "palm_hull_indices": [0, 1, 2, 5, 9, 13, 17]
    }

    out_file = landmarks_dir / "hand_landmarks_schema.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(landmarks_schema, f, indent=2, ensure_ascii=False)

    print(f"  -> Successfully generated {out_file.name} (21 landmarks).")


def main():
    print("================================================================")
    print("Running TASK-005 Reference Datasets Ingestion Pipeline...")
    print("================================================================")
    build_tarot_deck()
    build_tarot_spreads()
    build_palm_lines_catalog()
    build_palm_mounts_catalog()
    build_hand_landmarks_schema()
    print("================================================================")
    print("TASK-005 Reference Datasets Ingestion completed successfully!")
    print("================================================================")


if __name__ == "__main__":
    main()
