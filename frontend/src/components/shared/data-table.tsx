"use client";

import { useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown, SlidersHorizontal } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TableSkeleton } from "@/components/shared/states";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  /** Enable client-side sort on this column. */
  sortable?: boolean;
  /** Extract a comparable value for sorting (defaults to row[key]). */
  sortValue?: (row: T) => string | number;
  cell: (row: T) => ReactNode;
  className?: string;
  headClassName?: string;
  /** Hide by default in the column visibility menu. */
  defaultHidden?: boolean;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (row: T) => string | number;
  loading?: boolean;
  empty?: ReactNode;
  onRowClick?: (row: T) => void;
  /** Enable row selection + bulk actions. */
  selectable?: boolean;
  selectedIds?: Set<string | number>;
  onSelectionChange?: (ids: Set<string | number>) => void;
  bulkActions?: ReactNode;
  /** Show the column visibility toggle. */
  columnToggle?: boolean;
}

export function DataTable<T>({
  columns,
  data,
  rowKey,
  loading,
  empty,
  onRowClick,
  selectable,
  selectedIds,
  onSelectionChange,
  bulkActions,
  columnToggle = true,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(
    () => new Set(columns.filter((c) => c.defaultHidden).map((c) => c.key)),
  );

  const visibleColumns = columns.filter((c) => !hidden.has(c.key));

  const sortedData = useMemo(() => {
    if (!sort) return data;
    const col = columns.find((c) => c.key === sort.key);
    if (!col) return data;
    const getVal = col.sortValue ?? ((r: T) => (r as Record<string, unknown>)[sort.key] as string);
    return [...data].sort((a, b) => {
      const av = getVal(a) ?? "";
      const bv = getVal(b) ?? "";
      if (av < bv) return sort.dir === "asc" ? -1 : 1;
      if (av > bv) return sort.dir === "asc" ? 1 : -1;
      return 0;
    });
  }, [data, sort, columns]);

  const allSelected = selectable && data.length > 0 && data.every((r) => selectedIds?.has(rowKey(r)));
  const someSelected = selectable && !allSelected && data.some((r) => selectedIds?.has(rowKey(r)));

  function toggleAll() {
    if (!onSelectionChange) return;
    const next = new Set(selectedIds);
    if (allSelected) data.forEach((r) => next.delete(rowKey(r)));
    else data.forEach((r) => next.add(rowKey(r)));
    onSelectionChange(next);
  }

  function toggleRow(id: string | number) {
    if (!onSelectionChange) return;
    const next = new Set(selectedIds);
    next.has(id) ? next.delete(id) : next.add(id);
    onSelectionChange(next);
  }

  function toggleSort(key: string) {
    setSort((prev) => {
      if (prev?.key !== key) return { key, dir: "asc" };
      if (prev.dir === "asc") return { key, dir: "desc" };
      return null;
    });
  }

  if (loading) return <TableSkeleton cols={visibleColumns.length + (selectable ? 1 : 0)} />;

  const selectionCount = selectable
    ? data.filter((r) => selectedIds?.has(rowKey(r))).length
    : 0;

  return (
    <div className="space-y-2">
      {(columnToggle || (selectable && selectionCount > 0)) && (
        <div className="flex items-center justify-between">
          <div>
            {selectable && selectionCount > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium">{selectionCount} selected</span>
                {bulkActions}
              </div>
            )}
          </div>
          {columnToggle && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <SlidersHorizontal className="size-4" /> Columns
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>Toggle columns</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {columns.map((c) => (
                  <DropdownMenuCheckboxItem
                    key={c.key}
                    checked={!hidden.has(c.key)}
                    onCheckedChange={(checked) => {
                      setHidden((prev) => {
                        const next = new Set(prev);
                        checked ? next.delete(c.key) : next.add(c.key);
                        return next;
                      });
                    }}
                    onSelect={(e) => e.preventDefault()}
                  >
                    {c.header}
                  </DropdownMenuCheckboxItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      )}

      <div className="overflow-hidden rounded-xl border">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {selectable && (
                <TableHead className="w-10">
                  <Checkbox
                    checked={allSelected ? true : someSelected ? "indeterminate" : false}
                    onCheckedChange={toggleAll}
                    aria-label="Select all"
                  />
                </TableHead>
              )}
              {visibleColumns.map((c) => (
                <TableHead key={c.key} className={c.headClassName}>
                  {c.sortable ? (
                    <button
                      type="button"
                      onClick={() => toggleSort(c.key)}
                      className="inline-flex items-center gap-1 transition-colors hover:text-foreground"
                    >
                      {c.header}
                      {sort?.key === c.key ? (
                        sort.dir === "asc" ? (
                          <ArrowUp className="size-3.5" />
                        ) : (
                          <ArrowDown className="size-3.5" />
                        )
                      ) : (
                        <ChevronsUpDown className="size-3.5 opacity-40" />
                      )}
                    </button>
                  ) : (
                    c.header
                  )}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedData.length === 0 ? (
              <TableRow className="hover:bg-transparent">
                <TableCell
                  colSpan={visibleColumns.length + (selectable ? 1 : 0)}
                  className="h-40 p-0"
                >
                  {empty ?? (
                    <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
                      No records found.
                    </div>
                  )}
                </TableCell>
              </TableRow>
            ) : (
              sortedData.map((row) => {
                const id = rowKey(row);
                const selected = selectedIds?.has(id);
                return (
                  <TableRow
                    key={id}
                    data-state={selected ? "selected" : undefined}
                    className={cn(onRowClick && "cursor-pointer")}
                    onClick={() => onRowClick?.(row)}
                  >
                    {selectable && (
                      <TableCell onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={selected}
                          onCheckedChange={() => toggleRow(id)}
                          aria-label="Select row"
                        />
                      </TableCell>
                    )}
                    {visibleColumns.map((c) => (
                      <TableCell key={c.key} className={c.className}>
                        {c.cell(row)}
                      </TableCell>
                    ))}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
