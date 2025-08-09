import React from "react";
import ConfettiCannon from "react-native-confetti-cannon";

/**
 * Lightweight confetti helper for Expo.
 * Props:
 *  - fire: boolean (show/hide)
 *  - count: number (default 120)
 *  - origin: {x,y} (optional)
 *  - onEnd: () => void (optional)
 */
export default function Confetti({ fire, count = 120, origin = { x: -10, y: 0 }, onEnd }) {
  if (!fire) return null;
  return (
    <ConfettiCannon
      count={count}
      origin={origin}
      fadeOut
      onAnimationEnd={onEnd}
    />
  );
}
