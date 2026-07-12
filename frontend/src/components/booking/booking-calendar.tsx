"use client";

import { useMemo, useState } from "react";
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  parseISO,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BOOKING_STATUS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Booking } from "@/lib/api/types";

export function BookingCalendar({
  bookings,
  onSelect,
}: {
  bookings: Booking[];
  onSelect: (b: Booking) => void;
}) {
  const [cursor, setCursor] = useState(() => startOfMonth(new Date()));

  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(cursor), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(cursor), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [cursor]);

  const byDay = useMemo(() => {
    const map = new Map<string, Booking[]>();
    for (const b of bookings) {
      const key = format(parseISO(b.start_time), "yyyy-MM-dd");
      map.set(key, [...(map.get(key) ?? []), b]);
    }
    return map;
  }, [bookings]);

  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h3 className="text-sm font-semibold">{format(cursor, "MMMM yyyy")}</h3>
        <div className="flex items-center gap-1">
          <Button variant="outline" size="icon-sm" onClick={() => setCursor(addMonths(cursor, -1))}>
            <ChevronLeft className="size-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => setCursor(startOfMonth(new Date()))}>
            Today
          </Button>
          <Button variant="outline" size="icon-sm" onClick={() => setCursor(addMonths(cursor, 1))}>
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-7 border-b bg-muted/40 text-center text-xs font-medium text-muted-foreground">
        {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
          <div key={d} className="py-2">
            {d}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-7">
        {days.map((day) => {
          const key = format(day, "yyyy-MM-dd");
          const items = byDay.get(key) ?? [];
          const inMonth = isSameMonth(day, cursor);
          const today = isSameDay(day, new Date());
          return (
            <div
              key={key}
              className={cn(
                "min-h-[104px] border-b border-r p-1.5",
                !inMonth && "bg-muted/20 text-muted-foreground",
              )}
            >
              <div className="mb-1 flex justify-end">
                <span
                  className={cn(
                    "flex size-6 items-center justify-center rounded-full text-xs",
                    today && "bg-primary font-semibold text-primary-foreground",
                  )}
                >
                  {format(day, "d")}
                </span>
              </div>
              <div className="space-y-1">
                {items.slice(0, 3).map((b) => (
                  <button
                    key={b.id}
                    onClick={() => onSelect(b)}
                    className={cn(
                      "flex w-full items-center gap-1 truncate rounded px-1.5 py-0.5 text-left text-[11px] font-medium ring-1 ring-inset transition-opacity hover:opacity-80",
                      toneClass(b.status),
                    )}
                    title={b.purpose}
                  >
                    {format(parseISO(b.start_time), "HH:mm")} · {b.asset_id}
                  </button>
                ))}
                {items.length > 3 && (
                  <p className="px-1 text-[11px] text-muted-foreground">+{items.length - 3} more</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function toneClass(status: Booking["status"]) {
  const tone = BOOKING_STATUS[status].tone;
  switch (tone) {
    case "success":
      return "bg-success/10 text-success ring-success/20";
    case "warning":
      return "bg-warning/15 text-warning-foreground dark:text-warning ring-warning/25";
    case "danger":
      return "bg-destructive/10 text-destructive ring-destructive/20";
    case "primary":
      return "bg-primary/10 text-primary ring-primary/20";
    case "info":
      return "bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-blue-500/20";
    default:
      return "bg-muted text-muted-foreground ring-border";
  }
}
