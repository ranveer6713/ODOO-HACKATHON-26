"use client";

import { useMemo } from "react";
import { useCategories, useDepartments, useEmployees, useAssets } from "./use-entities";

/**
 * Resolves the local reference entities into id→record maps so tables can
 * render human labels for the string foreign keys used across the API.
 */
export function useLookups() {
  const deps = useDepartments({ page_size: 100 });
  const emps = useEmployees({ page_size: 100 });
  const cats = useCategories({ page_size: 100 });
  const assets = useAssets({ page_size: 100 });

  return useMemo(() => {
    const departments = new Map((deps.data?.items ?? []).map((d) => [d.id, d]));
    const employees = new Map((emps.data?.items ?? []).map((e) => [e.id, e]));
    const categories = new Map((cats.data?.items ?? []).map((c) => [c.id, c]));
    const assetMap = new Map((assets.data?.items ?? []).map((a) => [a.id, a]));

    return {
      departments,
      employees,
      categories,
      assets: assetMap,
      departmentName: (id?: string | null) => (id ? departments.get(id)?.name ?? id : "—"),
      employeeName: (id?: string | null) => (id ? employees.get(id)?.name ?? id : "—"),
      categoryName: (id?: string | null) => (id ? categories.get(id)?.name ?? id : "—"),
      assetName: (id?: string | null) => (id ? assetMap.get(id)?.name ?? id : "—"),
      assetTag: (id?: string | null) => (id ? assetMap.get(id)?.tag ?? id : "—"),
      isLoading: deps.isLoading || emps.isLoading || cats.isLoading || assets.isLoading,
    };
  }, [deps, emps, cats, assets]);
}
