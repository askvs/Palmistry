"""Train the hybrid ML recommender and persist artifacts (TASK-012).

Usage (from backend/ with the project venv):
    python scripts/train_recommender.py                 # content model only
    python scripts/train_recommender.py --with-db      # + item-item CF from feedback events
    python scripts/train_recommender.py --report       # print a training report

Artifacts are written to backend/models/recommender/recommender.joblib. The API
engine trains lazily from the catalog on first use, so training is an
optimisation + CF-inclusion step, not a hard requirement (D-017).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.recommendations.engine import (  # noqa: E402
    ENGINE_NAME,
    ENGINE_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
    HybridRecommendationEngine,
    default_artifact_path,
)
from app.services.recommendations.service import _load_collaborative_state  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the hybrid ML recommender")
    parser.add_argument(
        "--with-db",
        action="store_true",
        help="Also build item-item collaborative filtering from recommendation_events",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a training report (catalog + cluster summary)",
    )
    args = parser.parse_args()

    engine = HybridRecommendationEngine()

    cf_state = None
    if args.with_db:
        from app.db.session import get_engine
        from sqlalchemy.orm import Session

        with Session(get_engine()) as session:
            cf_state = _load_collaborative_state(session)

    artifact = engine.save(default_artifact_path())

    print(f"engine={ENGINE_NAME} v{ENGINE_VERSION} model={MODEL_NAME} v{MODEL_VERSION}")
    print(f"catalog_items={len(engine.catalog.items)}")
    print(f"vocabulary={len(engine.vectorizer.vocabulary_)}")
    print(f"clusters={int(engine.cluster_ids.max()) + 1 if engine.cluster_ids is not None else 0}")
    if cf_state is not None:
        print(
            f"collaborative: active={cf_state.active} "
            f"interactions={cf_state.positive_interactions} users={cf_state.user_count}"
        )
    else:
        print("collaborative: disabled (no usable feedback events or --with-db omitted)")
    print(f"artifact={artifact}")

    if args.report:
        try:
            import pandas as pd

            rows = [
                {
                    "item_id": item.id,
                    "type": item.type,
                    "cluster": int(engine.cluster_ids[row]) if engine.cluster_ids is not None else -1,
                    "effort": item.effort,
                    "horizon": item.horizon,
                    "title": item.title,
                }
                for row, item in enumerate(engine.catalog.items)
            ]
            frame = pd.DataFrame(rows)
            print("\nPer-type coverage:")
            print(frame["type"].value_counts().to_string())
            print("\nCluster sizes:")
            print(frame["cluster"].value_counts().sort_index().to_string())
        except Exception as exc:  # pragma: no cover - report-only path
            print(f"report skipped: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
