```
# Review Note — Evidence-Anchored

**Scope:** This PR introduces a `size` property to the Drawer component, setting width percentage and minWidth, and deprecates the `width` property.

## Problem
1. The deprecation of the `width` property is not fully backward compatible, potentially breaking existing implementations that rely on it.
2. The media query adjustments for smaller screens might not handle all edge cases, especially for very small devices.
3. The removal of the inline drawer feature could affect users who might still be using it, despite it being broken.

## Evidence
- `Drawer.tsx: line 45`: The `width` property is deprecated but still used in some instances, which could lead to confusion or errors.
- `Drawer.tsx: line 168`: The media query for smaller screens sets a fixed margin, which might not be suitable for all screen sizes.
- `Drawer.story.tsx: lines 22-56`: The inline drawer feature is removed, which might impact users who have not migrated away from it.

## Impact
- **Technical Impact:** Deprecating the `width` property without a clear migration path could lead to runtime errors or unexpected behavior in existing applications. The media query changes might not adequately address all screen sizes, leading to potential UI issues. Removing the inline drawer feature could break functionality for users who have not updated their code.

## Recommendation (Fix / Tests / Risks)
1. Provide a clear migration guide for users transitioning from `width` to `size`, including examples and potential pitfalls.
2. Test the media query changes on a variety of devices to ensure consistent behavior across different screen sizes.
3. Consider maintaining backward compatibility for the inline drawer feature or provide a clear deprecation notice with alternatives.

## Traceability
Not specified
```