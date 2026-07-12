"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";

/**
 * Lightweight deterministic QR-style visual for an asset tag. It renders a
 * stable matrix derived from the value (with finder patterns) so every asset
 * has a recognizable, printable code without pulling in a QR dependency.
 */
export function QrCode({
  value,
  size = 120,
  className,
}: {
  value: string;
  size?: number;
  className?: string;
}) {
  const cells = 21;
  const matrix = useMemo(() => buildMatrix(value, cells), [value]);
  const unit = size / cells;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={cn("rounded-md bg-white p-1", className)}
      role="img"
      aria-label={`QR code for ${value}`}
    >
      {matrix.map((row, y) =>
        row.map((on, x) =>
          on ? (
            <rect
              key={`${x}-${y}`}
              x={x * unit}
              y={y * unit}
              width={unit}
              height={unit}
              fill="#0d1117"
            />
          ) : null,
        ),
      )}
    </svg>
  );
}

function buildMatrix(value: string, size: number): boolean[][] {
  const grid: boolean[][] = Array.from({ length: size }, () =>
    Array.from({ length: size }, () => false),
  );

  // Deterministic pseudo-random fill from a simple string hash.
  let h = 2166136261;
  for (let i = 0; i < value.length; i++) {
    h ^= value.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      h ^= (x * 31 + y * 17 + h) & 0xffff;
      h = Math.imul(h, 16777619);
      grid[y][x] = ((h >>> 8) & 1) === 1;
    }
  }

  // Finder patterns (top-left, top-right, bottom-left).
  const placeFinder = (ox: number, oy: number) => {
    for (let y = 0; y < 7; y++) {
      for (let x = 0; x < 7; x++) {
        const border = x === 0 || x === 6 || y === 0 || y === 6;
        const core = x >= 2 && x <= 4 && y >= 2 && y <= 4;
        grid[oy + y][ox + x] = border || core;
      }
    }
    // Quiet ring
    for (let i = -1; i <= 7; i++) {
      if (oy + i >= 0 && oy + i < size && ox + 7 < size) grid[oy + i][ox + 7] = false;
      if (ox + i >= 0 && ox + i < size && oy + 7 < size) grid[oy + 7][ox + i] = false;
    }
  };
  placeFinder(0, 0);
  placeFinder(size - 7, 0);
  placeFinder(0, size - 7);

  return grid;
}
