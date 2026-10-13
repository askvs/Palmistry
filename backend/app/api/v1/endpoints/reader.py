@@
     # Aggregate spread popularity in Python.
-    spread_counts: dict[str, int] = {}
-    for (result,) in db.execute(select(Reading.result).where(Reading.type == "tarot")).all():
-        name = (result or {}).get("spread_name") if isinstance(result, dict) else None
-        if name:
-            spread_counts[str(name)] = spread_counts.get(str(name), 0) + 1
+    # Be tolerant to multiple historical shapes of Reading.result:
+    # - result["spread_name"] (canonical top-level)
+    # - result["interpretation"]["spread_name"] (interpretation payload)
+    # - result["spread"] (user-supplied spread string)
+    spread_counts: dict[str, int] = {}
+    for (result,) in db.execute(select(Reading.result).where(Reading.type == "tarot")).all():
+        if not isinstance(result, dict):
+            continue
+        name = result.get("spread_name")
+        if not name:
+            interp = result.get("interpretation")
+            if isinstance(interp, dict):
+                name = interp.get("spread_name")
+        if not name:
+            name = result.get("spread")
+        if not name:
+            continue
+        # Prefer using the raw user-provided spread string as the display label when available
+        display_label = result.get("spread") or str(name)
+        spread_counts[str(display_label)] = spread_counts.get(str(display_label), 0) + 1
     spread_rows = sorted(spread_counts.items(), key=lambda item: item[1], reverse=True)[:6]
