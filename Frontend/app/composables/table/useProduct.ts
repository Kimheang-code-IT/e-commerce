import { ref, computed, onMounted, watch } from "vue";
import type { TableColumn, DropdownMenuItem } from "@nuxt/ui";
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { Product, FormField } from "~/types";
import { formatCurrency } from "~/utils/format/currency";
import {
  useCategoryApi,
  useProductApi,
  useProductsViewApi,
} from "~/utils/api";
import type { ApiQueryParams } from "~/utils/api";
import { useServerTableResource } from "~/composables/table/useServerTableResource";
import { useMutation } from "~/composables/data/useMutation";

type ProductFormPayload = Omit<Product, "image"> & {
  image?: unknown;
  imageCurrent?: string;
};
type ProductApiPayload = {
  name: string;
  categoryId: string;
  inPrice: number;
  outPrice: number;
  commission: number;
  totalStock: number;
  inStock: number;
  sold: number;
  added: number;
  damaged: number;
  status: Product["status"];
  image?: string;
  stockNote?: string;
};

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error ?? new Error("read failed"));
    reader.readAsDataURL(file);
  });
}

export function useProduct() {
  /** Product table always uses REST CRUD; local mock list is not supported here. */
  const useBackendApi = computed(() => true);
  const productApi = useProductApi();
  const productsViewApi = useProductsViewApi();
  const categoryApi = useCategoryApi();
  const { formattedRange } = useGlobalFilter();
  const {
    t,
    toast,
    rowSelection,
    columnVisibility,
    isAnalyticsOpen,
    isFormOpen,
    isDetailOpen,
    isConfirmOpen,
  } = useBaseTable({});

  const { sorting, columnFilters, pagination, serverQuery } = useTableQuery({
    initialSorting: [{ id: "id", desc: false }],
  });
  const searchQuery = ref("");

  // --- Context States ---
  const selectedEntry = ref<Product | null>(null);
  const pendingEntry = ref<Product | null>(null);
  /** New image file chosen in the form; sent as data URL on save (backend persists under `/uploads`). */
  const pendingImageFile = ref<File | null>(null);
  const confirmMode = ref<"save" | "delete">("save");
  const isStockAdjustOpen = ref(false);
  const stockAdjustMode = ref<"added" | "damaged">("added");
  const stockAdjustQty = ref<number>(0);
  const stockAdjustNote = ref("");
  const stockAdjustTarget = ref<Product | null>(null);
  const isHistoryOpen = ref(false);
  const historyType = ref<"added" | "damaged">("added");
  const historyEntries = ref<any[]>([]);
  const isHistoryLoading = ref(false);
  const historyTotalRows = ref(0);
  const historyPagination = ref({ pageIndex: 0, pageSize: 50 });
  const historyDateRange = ref({
    start: undefined as any,
    end: undefined as any,
  });

  // --- Filter States ---
  const categoryItems = ref<{ label: string; value: string }[]>([]);
  const selectedCategories = ref<
    Array<string | { label: string; value: string }>
  >([]);

  function categoryFilterQueryValues(
    selected: Array<string | { label: string; value: string }>,
  ): string[] {
    return selected
      .map((s) =>
        s && typeof s === "object" && "value" in s
          ? String(s.value)
          : String(s),
      )
      .filter(Boolean);
  }

  // --- Mock Data ---
  const entries = ref<Product[]>([]);
  const mutation = useMutation();
  const mergedServerQuery = computed(() => ({
    ...serverQuery.value,
    search: searchQuery.value.trim() || undefined,
    dateFrom: formattedRange.value.start || undefined,
    dateTo: formattedRange.value.end || undefined,
    category:
      categoryFilterQueryValues(selectedCategories.value).join(",") ||
      undefined,
  }));
  watch(searchQuery, () => {
    pagination.value.pageIndex = 0;
  });
  const resource = useServerTableResource<Product, ApiQueryParams>({
    resourceKey: "products-view",
    useBackendApi,
    serverQuery: mergedServerQuery,
    localData: entries,
    listFn: (query, signal) => productsViewApi.list(query, signal),
    debounceMs: 220,
  });
  const effectiveEntries = computed(() => resource.rows.value);

  async function loadCategoryItems() {
    try {
      const res = await categoryApi.list({
        page: 1,
        limit: 200,
        sortBy: "name",
        sortOrder: "asc",
      });
      const items = (res.data || [])
        .map((item: any) => ({
          id: String(item?.id || "").trim(),
          name: String(item?.name || "").trim(),
        }))
        .filter((item: { id: string; name: string }) =>
          Boolean(item.id && item.name),
        );
      categoryItems.value = items.map((item) => ({
        label: item.name,
        value: item.id,
      }));
    } catch {
      categoryItems.value = [];
    }
  }

  onMounted(() => {
    loadCategoryItems();
  });

  // --- Computed ---
  const filteredEntries = computed(() => {
    const ids = categoryFilterQueryValues(selectedCategories.value);
    if (ids.length === 0) return effectiveEntries.value;
    return effectiveEntries.value.filter((e) =>
      ids.includes(String(e.categoryId || "")),
    );
  });

  const footerTotals = computed(() => {
    const data = filteredEntries.value;
    const sum = (key: keyof Product) =>
      data.reduce((total, item) => total + Number(item[key] || 0), 0);

    return {
      inPrice: formatCurrency(sum("inPrice"), "USD"),
      outPrice: formatCurrency(sum("outPrice"), "USD"),
      commission: formatCurrency(sum("commission"), "USD"),
      totalStock: sum("totalStock").toLocaleString(),
      inStock: sum("inStock").toLocaleString(),
      sold: sum("sold").toLocaleString(),
      added: sum("added").toLocaleString(),
      damaged: sum("damaged").toLocaleString(),
    };
  });

  const confirmConfig = computed(() => {
    if (confirmMode.value === "delete") {
      return {
        title: t("actions.delete"),
        description: `Are you sure you want to remove product #${selectedEntry.value?.id}? This action is permanent.`,
        type: "error" as const,
        submitLabel: t("actions.delete"),
        icon: "i-lucide-trash-2",
      };
    }
    return {
      title: selectedEntry.value
        ? t("pages.dataEntry.formTitleEdit")
        : t("pages.dataEntry.formTitleNew"),
      description: selectedEntry.value
        ? `Save changes to product #${pendingEntry.value?.id}?`
        : `Confirm adding new product "${pendingEntry.value?.name}"?`,
      type: "primary" as const,
      submitLabel: selectedEntry.value
        ? t("actions.save")
        : t("actions.confirm"),
      icon: "i-lucide-check-circle",
    };
  });

  // --- Configs ---
  const columns = computed<TableColumn<Product>[]>(() => [
    { accessorKey: "id", header: t("product.id") },
    { accessorKey: "image", header: t("product.image") },
    { accessorKey: "name", header: t("product.name") },
    { accessorKey: "category", header: t("product.category") },
    {
      accessorKey: "inPrice",
      header: t("product.inPrice"),
      footer: footerTotals.value.inPrice,
    },
    {
      accessorKey: "outPrice",
      header: t("product.outPrice"),
      footer: footerTotals.value.outPrice,
    },
    {
      accessorKey: "commission",
      header: t("product.commission"),
      footer: footerTotals.value.commission,
    },
    {
      accessorKey: "totalStock",
      header: t("product.totalStock"),
      footer: footerTotals.value.totalStock,
    },
    {
      accessorKey: "inStock",
      header: t("product.inStock"),
      footer: footerTotals.value.inStock,
    },
    {
      accessorKey: "sold",
      header: t("product.sold"),
      footer: footerTotals.value.sold,
    },
    {
      accessorKey: "added",
      header: t("product.added"),
      footer: footerTotals.value.added,
    },
    {
      accessorKey: "damaged",
      header: t("product.damaged"),
      footer: footerTotals.value.damaged,
    },
    { accessorKey: "status", header: t("product.status") },
    { accessorKey: "createdAt", header: t("product.createdAt") },
    { id: "action", header: t("common.actions") },
  ]);

  const entryFormFields = computed<FormField[]>(() => [
    {
      key: "image",
      label: t("product.image"),
      type: "file",
      placeholder: "Drop your image here",
      required: false,
    },
    {
      key: "name",
      label: t("product.name"),
      type: "input",
      placeholder: "ឧ. កុំព្យូទ័រយួរដៃ, គ្រឿងបន្លាស់",
      required: true,
    },
    {
      key: "categoryId",
      label: t("product.category"),
      type: "select",
      items: categoryItems.value,
      required: true,
    },
    {
      key: "inPrice",
      label: t("product.inPrice"),
      type: "number",
      placeholder: "0.00",
      required: true,
    },
    {
      key: "outPrice",
      label: t("product.outPrice"),
      type: "number",
      placeholder: "0.00",
      required: true,
    },
    {
      key: "commission",
      label: t("product.commission"),
      type: "number",
      placeholder: "0.00",
      required: false,
    },
    {
      key: "inStock",
      label: t("product.inStock"),
      type: "number",
      placeholder: "0",
      required: !Boolean(selectedEntry.value?.id),
      readonly: Boolean(selectedEntry.value?.id),
    },
    {
      key: "stockNote",
      label: t("product.note"),
      type: "textarea",
      placeholder: "Note...",
      required: false,
    },
  ]);

  // --- Row Actions ---
  function getDropdownActions(entry: Product): DropdownMenuItem[][] {
    return [
      [
        {
          label: t("actions.edit"),
          icon: "i-lucide-edit",
          onSelect: () => {
            selectedEntry.value = { ...entry };
            isFormOpen.value = true;
          },
        },

        {
          label: t("product.viewAddedStock"),
          icon: "i-lucide-history",
          onSelect: () => openHistory(entry, "added"),
        },
        {
          label: t("product.viewDamagedStock"),
          icon: "i-lucide-alert-circle",
          onSelect: () => openHistory(entry, "damaged"),
        },
        {
          label: t("actions.delete"),
          icon: "i-lucide-trash",
          color: "error" as const,
          onSelect: () => {
            selectedEntry.value = entry;
            confirmMode.value = "delete";
            isConfirmOpen.value = true;
          },
        },
      ],
    ];
  }

  function resolveFirstUploadFile(value: unknown): File | null {
    if (!value) return null;
    if (value instanceof File) return value;
    if (Array.isArray(value) && value.length > 0) {
      const first = value[0] as any;
      if (first instanceof File) return first;
      if (first?.file instanceof File) return first.file;
    }
    const record = value as any;
    if (record?.file instanceof File) return record.file;
    return null;
  }

  function resolveImageForSave(data: ProductFormPayload): string {
    const uploadedFile = resolveFirstUploadFile(data.image);
    if (uploadedFile) {
      // Local mode fallback: use object URL as previewable saved image.
      return URL.createObjectURL(uploadedFile);
    }

    const currentImage = String(data.imageCurrent || "").trim();
    const incomingImage = String(data.image || "").trim();

    // Edit mode: keep existing image if user did not select a new one.
    if (selectedEntry.value?.id) {
      if (currentImage) return currentImage;
      if (incomingImage) return incomingImage;
      return String(selectedEntry.value.image || "");
    }

    // New mode: use uploaded image if available, otherwise keep empty.
    return currentImage || incomingImage;
  }

  function handleSaveRequest(data: ProductFormPayload) {
    pendingImageFile.value = resolveFirstUploadFile(data.image);
    const { imageCurrent: _imageCurrent, ...restData } = data;
    const parsedInStock = Number(data.inStock ?? 0);
    const rawTotal = (data as Record<string, unknown>).totalStock;
    const totalStock =
      rawTotal !== undefined && rawTotal !== null && rawTotal !== ""
        ? Number(rawTotal)
        : parsedInStock;
    pendingEntry.value = {
      ...(restData as Partial<Product>),
      image: resolveImageForSave(data),
      inStock: parsedInStock,
      sold: Number(data.sold ?? 0),
      added: Number(data.added ?? 0),
      damaged: Number(data.damaged ?? 0),
      totalStock,
      inPrice: Number(data.inPrice ?? 0),
      outPrice: Number(data.outPrice ?? 0),
      commission: Number(data.commission ?? 0),
    } as Product;
    confirmMode.value = "save";
    isConfirmOpen.value = true;
  }

  function toProductApiPayload(
    data: Partial<Product> | null | undefined,
  ): ProductApiPayload {
    return {
      name: String(data?.name || "").trim(),
      categoryId: String(data?.categoryId ?? "").trim(),
      inPrice: Number(data?.inPrice ?? 0),
      outPrice: Number(data?.outPrice ?? 0),
      commission: Number(data?.commission ?? 0),
      totalStock: Number(data?.totalStock ?? 0),
      inStock: Number(data?.inStock ?? 0),
      sold: Number(data?.sold ?? 0),
      added: Number(data?.added ?? 0),
      damaged: Number(data?.damaged ?? 0),
      status: (String(data?.status || "active").trim() ||
        "active") as Product["status"],
      stockNote: (data as any)?.stockNote || undefined,
    };
  }

  async function toProductApiPayloadForSave(
    data: Partial<Product> | null | undefined,
    newImageFile: File | null,
  ): Promise<ProductApiPayload> {
    const base = toProductApiPayload(data);
    if (newImageFile) {
      base.image = await fileToDataUrl(newImageFile);
    }
    return base;
  }

  async function finalizeAction() {
    if (confirmMode.value === "delete" && selectedEntry.value) {
      await mutation.run(
        () => productApi.remove(selectedEntry.value!.id),
        "products-view",
      );
      await resource.refresh();
      toast.add({
        title: "Product Deleted",
        description: `Product #${selectedEntry.value.id} has been removed.`,
        color: "error",
      });
    } else if (confirmMode.value === "save" && pendingEntry.value) {
      const payload = await toProductApiPayloadForSave(
        pendingEntry.value,
        pendingImageFile.value,
      );
      pendingImageFile.value = null;
      if (!pendingEntry.value.id || pendingEntry.value.id === 0) {
        await mutation.run(() => productApi.create(payload), "products-view");
        await resource.refresh();
        toast.add({
          title: "Product Added",
          description: `New product added successfully.`,
          color: "primary",
        });
      } else {
        await mutation.run(
          () => productApi.update(pendingEntry.value!.id, payload),
          "products-view",
        );
        await resource.refresh();
        toast.add({
          title: "Product Updated",
          description: `Product #${pendingEntry.value.id} updated.`,
          color: "primary",
        });
      }
    }
    isConfirmOpen.value = false;
    isFormOpen.value = false;
    selectedEntry.value = null;
    pendingEntry.value = null;
  }

  function handleAddNew() {
    selectedEntry.value = null;
    pendingImageFile.value = null;
    isFormOpen.value = true;
  }

  function openStockAdjustDialog(entry: Product, mode: "added" | "damaged") {
    stockAdjustTarget.value = entry;
    stockAdjustMode.value = mode;
    stockAdjustQty.value = 0;
    isStockAdjustOpen.value = true;
  }

  async function applyStockAdjust() {
    const target = stockAdjustTarget.value;
    const qty = Number(stockAdjustQty.value);
    if (!target || !Number.isFinite(qty) || qty <= 0) return;

    const deltaAdded = stockAdjustMode.value === "added" ? qty : 0;
    const deltaDamaged = stockAdjustMode.value === "damaged" ? qty : 0;

    const nextAdded = Number(target.added || 0) + deltaAdded;
    const nextDamaged = Number(target.damaged || 0) + deltaDamaged;
    const nextInStock = Number(target.inStock || 0) + deltaAdded - deltaDamaged;
    const nextTotalStock = Number(target.totalStock || 0) + deltaAdded;

    const payload = toProductApiPayload({
      ...target,
      added: nextAdded,
      damaged: nextDamaged,
      inStock: nextInStock,
      totalStock: nextTotalStock,
      stockNote: stockAdjustNote.value,
    });

    await productApi.update(target.id, payload);
    await resource.refresh();

    toast.add({
      title:
        stockAdjustMode.value === "added"
          ? "Stock Added"
          : "Damaged Stock Added",
      description: `Updated product #${target.id}`,
      color: stockAdjustMode.value === "added" ? "primary" : "warning",
    });

    isStockAdjustOpen.value = false;
    stockAdjustTarget.value = null;
    stockAdjustQty.value = 0;
    stockAdjustNote.value = "";
  }

  async function openHistory(entry: Product, type: "added" | "damaged") {
    selectedEntry.value = entry;
    historyType.value = type;
    historyPagination.value.pageIndex = 0;
    isHistoryOpen.value = true;
    await loadHistory();
  }

  async function loadHistory() {
    if (!selectedEntry.value) return;
    isHistoryLoading.value = true;
    try {
      const toISO = (val: any) => {
        if (!val) return undefined;
        const d = new Date(val);
        return isNaN(d.getTime()) ? undefined : d.toISOString();
      };

      const params: ApiQueryParams = {
        page: historyPagination.value.pageIndex + 1,
        limit: historyPagination.value.pageSize,
        dateFrom: toISO(historyDateRange.value.start),
        dateTo: toISO(historyDateRange.value.end),
      };
      const res =
        historyType.value === "added"
          ? await productApi.listStockAdditions(selectedEntry.value.id, params)
          : await productApi.listDamages(selectedEntry.value.id, params);

      if (res) {
        historyEntries.value = res.data || [];
        historyTotalRows.value = res.total || 0;
      }
    } catch (err) {
      console.error("Failed to load history:", err);
      toast.add({ title: "Failed to load history", color: "error" });
    } finally {
      isHistoryLoading.value = false;
    }
  }

  watch(
    [historyPagination, historyDateRange],
    () => {
      if (isHistoryOpen.value) loadHistory();
    },
    { deep: true },
  );

  return {
    // Table States
    rowSelection,
    sorting,
    searchQuery,
    columnVisibility,
    columnFilters,
    pagination,
    // Overlay States
    isAnalyticsOpen,
    isFormOpen,
    isConfirmOpen,
    isStockAdjustOpen,
    selectedEntry,
    // Filters
    categoryItems,
    selectedCategories,
    entries: effectiveEntries,
    totalRows: resource.totalRows,
    isLoading: resource.isLoading,
    // Computed/Configs
    filteredEntries,
    confirmConfig,
    columns,
    entryFormFields,
    // Actions
    getDropdownActions,
    handleSaveRequest,
    finalizeAction,
    handleAddNew,
    stockAdjustMode,
    stockAdjustQty,
    stockAdjustNote,
    stockAdjustTarget,
    openStockAdjustDialog,
    applyStockAdjust,
    // History
    isHistoryOpen,
    historyType,
    historyEntries,
    isHistoryLoading,
    historyTotalRows,
    historyPagination,
    historyDateRange,
    openHistory,
    loadHistory,
  };
}
