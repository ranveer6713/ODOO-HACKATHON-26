"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { localStore } from "@/lib/api/local-store";
import type {
  Allocation,
  Asset,
  AssetCategory,
  Department,
  Employee,
  Transfer,
} from "@/lib/api/types";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

type Params = Record<string, unknown>;

function useInvalidateEntities() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["entities"] });
}

// -------------------------------------------------------------------------
// Departments
// -------------------------------------------------------------------------
export function useDepartments(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.departments(params),
    queryFn: () => localStore.departments.list(params),
  });
}

export function useDepartmentMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (body: Omit<Department, "id" | "created_at">) =>
      localStore.departments.create(body),
    onSuccess: () => {
      toast.success("Department created");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<Department> }) =>
      localStore.departments.update(id, body),
    onSuccess: () => {
      toast.success("Department updated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const remove = useMutation({
    mutationFn: (id: string) => localStore.departments.remove(id),
    onSuccess: () => {
      toast.success("Department deleted");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, update, remove };
}

// -------------------------------------------------------------------------
// Employees
// -------------------------------------------------------------------------
export function useEmployees(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.employees(params),
    queryFn: () => localStore.employees.list(params),
  });
}

export function useEmployeeMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (body: Omit<Employee, "id" | "created_at">) =>
      localStore.employees.create(body),
    onSuccess: () => {
      toast.success("Employee added");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<Employee> }) =>
      localStore.employees.update(id, body),
    onSuccess: () => {
      toast.success("Employee updated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const remove = useMutation({
    mutationFn: (id: string) => localStore.employees.remove(id),
    onSuccess: () => {
      toast.success("Employee removed");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, update, remove };
}

// -------------------------------------------------------------------------
// Categories
// -------------------------------------------------------------------------
export function useCategories(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.categories(params),
    queryFn: () => localStore.categories.list(params),
  });
}

export function useCategoryMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (body: Omit<AssetCategory, "id" | "created_at">) =>
      localStore.categories.create(body),
    onSuccess: () => {
      toast.success("Category created");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<AssetCategory> }) =>
      localStore.categories.update(id, body),
    onSuccess: () => {
      toast.success("Category updated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const remove = useMutation({
    mutationFn: (id: string) => localStore.categories.remove(id),
    onSuccess: () => {
      toast.success("Category deleted");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, update, remove };
}

// -------------------------------------------------------------------------
// Assets
// -------------------------------------------------------------------------
export function useAssets(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.assets(params),
    queryFn: () => localStore.assets.list(params),
  });
}

export function useAsset(id: string, enabled = true) {
  return useQuery({
    queryKey: qk.entities.asset(id),
    queryFn: () => localStore.assets.get(id),
    enabled: enabled && !!id,
  });
}

export function useAssetMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (body: Omit<Asset, "id" | "tag" | "created_at" | "updated_at">) =>
      localStore.assets.create(body),
    onSuccess: () => {
      toast.success("Asset registered");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<Asset> }) =>
      localStore.assets.update(id, body),
    onSuccess: () => {
      toast.success("Asset updated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const remove = useMutation({
    mutationFn: (id: string) => localStore.assets.remove(id),
    onSuccess: () => {
      toast.success("Asset deleted");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, update, remove };
}

// -------------------------------------------------------------------------
// Allocations
// -------------------------------------------------------------------------
export function useAllocations(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.allocations(params),
    queryFn: () => localStore.allocations.list(params),
  });
}

export function useAllocationMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (body: Pick<Allocation, "asset_id" | "employee_id" | "notes">) =>
      localStore.allocations.create(body),
    onSuccess: () => {
      toast.success("Asset allocated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const returnAsset = useMutation({
    mutationFn: (id: string) => localStore.allocations.returnAsset(id),
    onSuccess: () => {
      toast.success("Asset returned");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, returnAsset };
}

// -------------------------------------------------------------------------
// Transfers
// -------------------------------------------------------------------------
export function useTransfers(params: Params = {}) {
  return useQuery({
    queryKey: qk.entities.transfers(params),
    queryFn: () => localStore.transfers.list(params),
  });
}

export function useTransferMutations() {
  const invalidate = useInvalidateEntities();
  const create = useMutation({
    mutationFn: (
      body: Pick<Transfer, "asset_id" | "from_department_id" | "to_department_id" | "reason" | "requested_by">,
    ) => localStore.transfers.create(body),
    onSuccess: () => {
      toast.success("Transfer requested");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: Transfer["status"] }) =>
      localStore.transfers.setStatus(id, status),
    onSuccess: () => {
      toast.success("Transfer updated");
      invalidate();
    },
    onError: (e) => toastError(e),
  });
  return { create, setStatus };
}
