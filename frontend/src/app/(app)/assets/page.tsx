"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
  Download,
  Eye,
  MoreHorizontal,
  Package,
  Pencil,
  Plus,
  QrCode as QrIcon,
  Trash2,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { SearchInput } from "@/components/shared/search-input";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { QrCode } from "@/components/shared/qr-code";
import { AssetFormSheet } from "@/components/assets/asset-form-sheet";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { useAssets, useAssetMutations, useCategories, useDepartments } from "@/lib/hooks/use-entities";
import { ASSET_STATUS, PAGE_SIZE } from "@/lib/constants";
import { downloadBlob, formatDate, formatNumber } from "@/lib/utils";
import type { Asset, AssetStatus } from "@/lib/api/types";

const STATUS_KEYS = Object.keys(ASSET_STATUS) as AssetStatus[];

export default function AssetsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("all");
  const [dept, setDept] = useState("all");
  const [page, setPage] = useState(1);
  const debounced = useDebounce(search);

  const params = useMemo(
    () => ({
      search: debounced || undefined,
      status: status === "all" ? undefined : status,
      category_id: category === "all" ? undefined : category,
      department_id: dept === "all" ? undefined : dept,
      page,
      page_size: PAGE_SIZE,
    }),
    [debounced, status, category, dept, page],
  );

  const { data, isLoading } = useAssets(params);
  const { data: categories } = useCategories({ page_size: 100 });
  const { data: departments } = useDepartments({ page_size: 100 });
  const { remove } = useAssetMutations();

  const [selected, setSelected] = useState<Set<string | number>>(new Set());
  const [sheetOpen, setSheetOpen] = useState(false);
  const [editing, setEditing] = useState<Asset | null>(null);
  const [toDelete, setToDelete] = useState<Asset | null>(null);
  const [bulkDelete, setBulkDelete] = useState(false);
  const [qrAsset, setQrAsset] = useState<Asset | null>(null);

  const categoryName = (id: string) => categories?.items.find((c) => c.id === id)?.name ?? id;

  function openCreate() {
    setEditing(null);
    setSheetOpen(true);
  }
  function openEdit(a: Asset) {
    setEditing(a);
    setSheetOpen(true);
  }

  function exportCsv(rows: Asset[]) {
    const header = ["Tag", "Name", "Category", "Status", "Serial", "Location", "Cost"];
    const lines = rows.map((a) =>
      [a.tag, a.name, categoryName(a.category_id), a.status, a.serial_number, a.location, a.purchase_cost].join(","),
    );
    const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" });
    downloadBlob(blob, "assets.csv");
    toast.success(`Exported ${rows.length} assets`);
  }

  const columns: Column<Asset>[] = [
    {
      key: "name",
      header: "Asset",
      sortable: true,
      cell: (a) => (
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-lg bg-muted text-muted-foreground">
            <Package className="size-4.5" />
          </div>
          <div>
            <p className="font-medium">{a.name}</p>
            <p className="font-mono text-xs text-muted-foreground">{a.tag}</p>
          </div>
        </div>
      ),
    },
    { key: "category", header: "Category", cell: (a) => categoryName(a.category_id) },
    {
      key: "status",
      header: "Status",
      sortable: true,
      cell: (a) => <StatusBadge meta={ASSET_STATUS[a.status]} />,
    },
    {
      key: "serial_number",
      header: "Serial",
      defaultHidden: true,
      cell: (a) => <span className="font-mono text-xs">{a.serial_number}</span>,
    },
    { key: "location", header: "Location", cell: (a) => a.location || "—" },
    {
      key: "purchase_cost",
      header: "Value",
      sortable: true,
      sortValue: (a) => a.purchase_cost,
      cell: (a) => <span className="tabular-nums">${formatNumber(a.purchase_cost)}</span>,
    },
    {
      key: "purchase_date",
      header: "Purchased",
      defaultHidden: true,
      cell: (a) => <span className="text-muted-foreground">{formatDate(a.purchase_date)}</span>,
    },
    {
      key: "actions",
      header: "",
      headClassName: "w-10",
      cell: (a) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" onClick={(e) => e.stopPropagation()}>
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => router.push(`/assets/${a.id}`)}>
              <Eye className="size-4" /> View details
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => openEdit(a)}>
              <Pencil className="size-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setQrAsset(a)}>
              <QrIcon className="size-4" /> QR code
            </DropdownMenuItem>
            <DropdownMenuItem destructive onClick={() => setToDelete(a)}>
              <Trash2 className="size-4" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const selectedRows = (data?.items ?? []).filter((a) => selected.has(a.id));

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assets"
        description="The complete register of assets across your organization."
        actions={
          <>
            <Button variant="outline" onClick={() => exportCsv(data?.items ?? [])}>
              <Download className="size-4" /> Export
            </Button>
            <Button onClick={openCreate}>
              <Plus className="size-4" /> Register Asset
            </Button>
          </>
        }
      />

      <Card className="grid grid-cols-1 gap-3 p-4 md:grid-cols-4">
        <SearchInput
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(1);
          }}
          placeholder="Search name, tag, serial…"
        />
        <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {STATUS_KEYS.map((s) => (
              <SelectItem key={s} value={s}>
                {ASSET_STATUS[s].label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={category} onValueChange={(v) => { setCategory(v); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {categories?.items.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={dept} onValueChange={(v) => { setDept(v); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Department" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All departments</SelectItem>
            {departments?.items.map((d) => (
              <SelectItem key={d.id} value={d.id}>
                {d.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        rowKey={(a) => a.id}
        loading={isLoading}
        selectable
        selectedIds={selected}
        onSelectionChange={setSelected}
        onRowClick={(a) => router.push(`/assets/${a.id}`)}
        bulkActions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => exportCsv(selectedRows)}>
              <Download className="size-4" /> Export
            </Button>
            <Button variant="outline" size="sm" className="text-destructive" onClick={() => setBulkDelete(true)}>
              <Trash2 className="size-4" /> Delete
            </Button>
          </div>
        }
        empty={
          <EmptyState
            icon={Package}
            title="No assets found"
            description="Try adjusting your filters, or register a new asset."
            action={
              <Button onClick={openCreate}>
                <Plus className="size-4" /> Register Asset
              </Button>
            }
          />
        }
      />
      <Pagination meta={data?.meta} onPageChange={setPage} />

      <AssetFormSheet open={sheetOpen} onOpenChange={setSheetOpen} asset={editing} />

      {/* QR dialog */}
      <Dialog open={!!qrAsset} onOpenChange={(o) => !o && setQrAsset(null)}>
        <DialogContent className="max-w-xs">
          <DialogHeader>
            <DialogTitle>Asset QR Code</DialogTitle>
          </DialogHeader>
          {qrAsset && (
            <div className="flex flex-col items-center gap-3 pb-2">
              <QrCode value={qrAsset.tag} size={180} />
              <div className="text-center">
                <p className="font-medium">{qrAsset.name}</p>
                <p className="font-mono text-sm text-muted-foreground">{qrAsset.tag}</p>
              </div>
              <Button variant="outline" size="sm" className="w-full" onClick={() => window.print()}>
                <QrIcon className="size-4" /> Print label
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete asset?"
        description={`This permanently removes “${toDelete?.name}” (${toDelete?.tag}).`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id, { onSuccess: () => setToDelete(null) })}
      />

      <ConfirmDialog
        open={bulkDelete}
        onOpenChange={setBulkDelete}
        title={`Delete ${selected.size} assets?`}
        description="This action cannot be undone."
        confirmLabel="Delete all"
        destructive
        onConfirm={async () => {
          for (const id of selected) await remove.mutateAsync(String(id));
          setSelected(new Set());
          setBulkDelete(false);
        }}
      />
    </div>
  );
}
