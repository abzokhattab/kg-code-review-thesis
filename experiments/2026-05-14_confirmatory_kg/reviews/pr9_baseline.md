# Review Note — Evidence-Anchored

**Scope:** This PR fixes a regression in Android plugin signal connections by implementing the `_get` method in `JNISingleton` to allow signals to be accessed as properties, and adds a new test case to verify this functionality.

## Problem
1.  **Narrow Scope of `_get` Implementation:** The `_get` method in `JNISingleton` is implemented to exclusively handle signals. While this directly addresses the reported regression, `_get` is a general mechanism for dynamic property access in Godot. If `JNISingleton` were to expose other non-signal properties in the future (e.g., via `ClassDB::bind_property` or other dynamic means), they would not be accessible via this `_get` implementation, potentially requiring further modifications or leading to similar "Invalid access" errors for those properties. This makes the `JNISingleton`'s property access behavior inconsistent with typical Godot `Object`s that might expose both signals and other properties via `_get`.
2.  **Potential for Future Property/Signal Name Collisions:** The current `_get` implementation prioritizes returning a `Signal` object if a property name matches a registered signal. While this is generally desired for signal access, if `JNISingleton` were to bind a regular property (via `ClassDB::bind_property`) with the same name as a signal, the signal would take precedence when accessed via `_plugin.property_name`. This is a minor concern as `JNISingleton` typically doesn't bind many properties, but it's a design consideration for future extensions.

## Evidence
*   `platform/android/api/jni_singleton.cpp:36-41` (New `_get` implementation only checks `has_signal`)
*   `platform/android/api/jni_singleton.h:49` (Declaration of `_get` method)

## Impact
*   **Inconsistent API Behavior:** Future attempts to expose non-signal properties on `JNISingleton` via `_get` would fail, requiring developers to remember this specific limitation or implement workarounds. This could lead to confusion and unexpected runtime errors for plugin developers.
*   **Maintenance Overhead:** If `JNISingleton` evolves to include more dynamic properties, the `_get` method would need to be continually updated, potentially leading to a fragmented property access mechanism.
*   **Subtle Bugs:** In the unlikely event of a property/signal name collision, the signal taking precedence could lead to subtle bugs where a developer expects to retrieve a property value but instead gets a `Signal` object.

## Recommendation (Fix / Tests / Risks)
1.  **Enhance `_get` for General Property Access (Fix):** Consider extending the `_get` method to handle other potential dynamic properties of `JNISingleton` beyond just signals. This might involve checking `ClassDB` for bound properties or other internal mechanisms if `JNISingleton` is expected to expose more than just signals dynamically. If no other dynamic properties are anticipated, add a comment explaining the intentional narrow scope.
2.  **Document `_get` Behavior (Risk Mitigation):** Clearly document the specific behavior of `JNISingleton`'s `_get` method, stating that it currently only resolves signals. This will inform future developers about its limitations and prevent unexpected behavior.
3.  **Add Test for Non-Signal Property Access (Tests):** While not directly failing with this PR, consider adding a test case that attempts to access a non-existent property or a hypothetical non-signal property via `_get` to ensure it correctly returns `false` or handles it gracefully, reinforcing the intended behavior.

## Traceability
Not specified