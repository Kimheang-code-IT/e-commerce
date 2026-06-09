import { ref, computed, onMounted, watch } from "vue";
import type { TableColumn, DropdownMenuItem } from "@nuxt/ui";
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { Product, FormField } from "~/types";
import { formatCurrency } from "~/utils/format/currency";
import {
  useProductApi,
  useProductsViewApi,
  useSupplierApi,
} from "~/utils/api";
import type { ApiQueryParams } from "~/utils/api";
import { useServerTableResource } from "~/composables/table/useServerTableResource";
import { useMutation } from "~/composables/data/useMutation";
import { useCategoryOptions } from "~/composables/data/useCategoryOptions";

type ProductFormPayload = Omit<Product, "image"> & {
  image?: unknown;
  imageCurrent?: string;
};
type ProductApiPayload = {
  name: string;
  model?: string;
  discountPrice?: number;
  totalPrice?: number;
  size?: string;
  top?: string;
  backSide?: string;
  fretboard?: string;
  string?: string;
  finishing?: string;
  color?: string;
  categoryId: string;
  supplierId?: number;
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
  const supplierApi = useSupplierApi();
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
  const perms = useModulePermissions('product');

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
  const stockAdjustInPrice = ref<number>(0);
  const stockAdjustOutPrice = ref<number>(0);
  const stockAdjustNote = ref("");
  const stockAdjustTarget = ref<Product | null>(null);
  const stockAdjustLotId = ref<number | null>(null);
  const stockLotOptions = ref<{ label: string; value: number; qtyRemaining: number }[]>([]);
  const isStockLotsLoading = ref(false);
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
  const { items: categoryItems } = useCategoryOptions();
  const supplierItems = ref<{ label: string; value: string }[]>([]);
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
  watch(selectedCategories, () => {
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

  onMounted(() => {
    loadSupplierItems();
  });

  async function loadSupplierItems() {
    try {
      const res = await supplierApi.list({
        page: 1,
        limit: 200,
        sortBy: "name",
        sortOrder: "asc",
      });
      supplierItems.value = (res.data || [])
        .map((item: any) => ({
          label: String(item?.name || "").trim(),
          value: String(item?.id || "").trim(),
        }))
        .filter((item: { label: string; value: string }) => Boolean(item.label && item.value));
    } catch {
      supplierItems.value = [];
    }
  }

  async function resolveSupplierIdForProduct(entry: Product): Promise<number | undefined> {
    const currentSupplierId =
      entry.supplierId !== undefined && entry.supplierId !== null && String(entry.supplierId).trim()
        ? Number(entry.supplierId)
        : undefined;
    if (currentSupplierId) return currentSupplierId;

    const productName = String(entry.name || "").trim().toLowerCase();
    if (!productName) return undefined;

    const suppliers = supplierItems.value
      .map((item) => Number(item.value))
      .filter((id) => Number.isFinite(id));

    for (const supplierId of suppliers) {
      try {
        const res = await supplierApi.listProducts(supplierId, { page: 1, limit: 200 });
        const match = (res.data || []).find(
          (p: any) => String(p?.productName || "").trim().toLowerCase() === productName,
        );
        if (match) return supplierId;
      } catch {
        // Ignore per-supplier lookup errors and continue scanning.
      }
    }
    return undefined;
  }

  const footerTotals = computed(() => {
    const data = effectiveEntries.value;
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
        titleKey: "pages.product.confirmDeleteTitle",
        description: t("pages.product.confirmDeleteDesc", {
          id: selectedEntry.value?.id ?? "",
        }),
        type: "error" as const,
        submitLabelKey: "actions.delete",
        icon: "i-lucide-trash-2",
      };
    }
    const isEdit = Boolean(selectedEntry.value);
    return {
      titleKey: isEdit
        ? "pages.product.confirmEditTitle"
        : "pages.product.confirmNewTitle",
      description: isEdit
        ? t("pages.product.confirmEditDesc", {
            id: pendingEntry.value?.id ?? "",
          })
        : t("pages.product.confirmNewDesc", {
            name: pendingEntry.value?.name ?? "",
          }),
      type: "primary" as const,
      submitLabelKey: isEdit ? "actions.save" : "actions.confirm",
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
      textRule: "text",
    },
    {
      key: "model",
      label: t("product.model"),
      type: "input",
      placeholder: t("product.modelPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "discountPrice",
      label: t("product.discountPrice"),
      type: "currency",
      placeholder: "0.00",
      required: false,
      min: 0,
      currencyPrefix: "USD",
    },
    {
      key: "totalPrice",
      label: t("product.totalPrice"),
      type: "currency",
      placeholder: "0.00",
      required: false,
      min: 0,
      currencyPrefix: "USD",
    },
    {
      key: "size",
      label: t("product.size"),
      type: "input",
      placeholder: t("product.sizePlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "top",
      label: t("product.top"),
      type: "input",
      placeholder: t("product.topPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "backSide",
      label: t("product.backSide"),
      type: "input",
      placeholder: t("product.backSidePlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "fretboard",
      label: t("product.fretboard"),
      type: "input",
      placeholder: t("product.fretboardPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "string",
      label: t("product.string"),
      type: "input",
      placeholder: t("product.stringPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "finishing",
      label: t("product.finishing"),
      type: "input",
      placeholder: t("product.finishingPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "color",
      label: t("product.color"),
      type: "input",
      placeholder: t("product.colorPlaceholder"),
      required: false,
      textRule: "text",
    },
    {
      key: "categoryId",
      label: t("product.category"),
      type: "select",
      items: categoryItems.value,
      required: true,
    },
    {
      key: "supplierId",
      label: "Supplier",
      type: "select",
      items: supplierItems.value,
      required: false,
    },
    {
      key: "inPrice",
      label: t("product.inPrice"),
      type: "currency",
      placeholder: "0.00",
      required: true,
      min: 0,
      currencyPrefix: "USD",
    },
    {
      key: "outPrice",
      label: t("product.outPrice"),
      type: "currency",
      placeholder: "0.00",
      required: true,
      min: 0,
      currencyPrefix: "USD",
    },
    {
      key: "commission",
      label: t("product.commission"),
      type: "money-tabs",
      refPriceKey: "outPrice",
      placeholder: "0.00",
      required: false,
      min: 0,
    },
    {
      key: "inStock",
      label: t("product.inStock"),
      type: "number",
      placeholder: "0",
      required: !Boolean(selectedEntry.value?.id),
      readonly: false,
    },
    {
      key: "stockNote",
      label: t("product.note"),
      type: "textarea",
      placeholder: "Note...",
      required: false,
      textRule: "text",
    },
  ]);

  // --- Row Actions ---
  function getDropdownActions(entry: Product): DropdownMenuItem[][] {
    const items: DropdownMenuItem[] = [];
    if (perms.canUpdate.value) {
      items.push({
        label: t("actions.edit"),
        icon: "i-lucide-edit",
        onSelect: async () => {
          const resolvedSupplierId = await resolveSupplierIdForProduct(entry);
          selectedEntry.value = {
            ...entry,
            supplierId: resolvedSupplierId,
          };
          isFormOpen.value = true;
        },
      });
    }
    if (perms.canViewAdjustStock.value) {
      items.push({
        label: t("product.viewAddedStock"),
        icon: "i-lucide-history",
        onSelect: () => openHistory(entry, "added"),
      });
    }
    if (perms.canViewAddDamage.value) {
      items.push({
        label: t("product.viewDamagedStock"),
        icon: "i-lucide-alert-circle",
        onSelect: () => openHistory(entry, "damaged"),
      });
    }
    if (perms.canDelete.value) {
      items.push({
        label: t("actions.delete"),
        icon: "i-lucide-trash",
        color: "error" as const,
        onSelect: () => {
          selectedEntry.value = entry;
          confirmMode.value = "delete";
          isConfirmOpen.value = true;
        },
      });
    }
    return items.length ? [items] : [];
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
    // Keep total stock synchronized with current in-stock value.
    const totalStock = parsedInStock;
    pendingEntry.value = {
      ...(restData as Partial<Product>),
      image: resolveImageForSave(data),
      supplierId:
        data.supplierId !== undefined && data.supplierId !== null && String(data.supplierId).trim()
          ? Number(data.supplierId)
          : undefined,
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
      model: String(data?.model || "").trim(),
      discountPrice: Number(data?.discountPrice ?? 0),
      totalPrice: Number(data?.totalPrice ?? data?.outPrice ?? 0),
      size: String(data?.size || "").trim(),
      top: String(data?.top || "").trim(),
      backSide: String(data?.backSide || "").trim(),
      fretboard: String(data?.fretboard || "").trim(),
      string: String(data?.string || "").trim(),
      finishing: String(data?.finishing || "").trim(),
      color: String(data?.color || "").trim(),
      categoryId: String(data?.categoryId ?? "").trim(),
      supplierId:
        data?.supplierId !== undefined && data?.supplierId !== null && String(data.supplierId).trim()
          ? Number(data.supplierId)
          : undefined,
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
      await resource.load();
      toast.add({
        title: t("pages.product.toastDeleted"),
        description: t("pages.product.toastDeletedDesc", {
          id: selectedEntry.value.id,
        }),
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
        await resource.load();
        toast.add({
          title: t("pages.product.toastAdded"),
          description: t("pages.product.toastAddedDesc"),
          color: "primary",
        });
      } else {
        await mutation.run(
          () => productApi.update(pendingEntry.value!.id, payload),
          "products-view",
        );
        await resource.load();
        toast.add({
          title: t("pages.product.toastUpdated"),
          description: t("pages.product.toastUpdatedDesc", {
            id: pendingEntry.value.id,
          }),
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
    if (!perms.canCreate.value) return;
    selectedEntry.value = null;
    pendingImageFile.value = null;
    isFormOpen.value = true;
  }

  async function loadOpenStockLots(productId: number) {
    isStockLotsLoading.value = true;
    stockLotOptions.value = [];
    stockAdjustLotId.value = null;
    try {
      const res = await productApi.listOpenStockLots(productId);
      const rows = Array.isArray(res?.data) ? res.data : [];
      stockLotOptions.value = rows.map((lot: any) => {
        const left = Number(lot.qtyRemaining ?? lot.qty ?? 0);
        const inP = Number(lot.inPrice ?? 0);
        const outP = Number(lot.outPrice ?? 0);
        return {
          value: Number(lot.id),
          qtyRemaining: left,
          label: `#${lot.id} · ${left} ${t("components.stockAdjust.lotQtyLeft")} · $${inP.toFixed(2)} / $${outP.toFixed(2)}`,
        };
      });
      stockAdjustLotId.value = stockLotOptions.value[0]?.value ?? null;
    } catch {
      stockLotOptions.value = [];
      stockAdjustLotId.value = null;
    } finally {
      isStockLotsLoading.value = false;
    }
  }

  async function openStockAdjustDialog(entry: Product, mode: "added" | "damaged") {
    if (mode === "added" && !perms.canAdjustStock.value) return;
    if (mode === "damaged" && !perms.canAddDamage.value) return;
    stockAdjustTarget.value = entry;
    stockAdjustMode.value = mode;
    stockAdjustQty.value = 0;
    stockAdjustInPrice.value = Number(entry.inPrice || 0);
    stockAdjustOutPrice.value = Number(entry.salePrice ?? entry.outPrice ?? 0);
    stockAdjustNote.value = "";
    stockAdjustLotId.value = null;
    stockLotOptions.value = [];
    if (mode === "damaged") {
      await loadOpenStockLots(entry.id);
    }
    isStockAdjustOpen.value = true;
  }

  async function applyStockAdjust() {
    const target = stockAdjustTarget.value;
    const qty = Number(stockAdjustQty.value);
    if (!target || !Number.isFinite(qty) || qty <= 0) return;

    if (stockAdjustMode.value === "damaged") {
      if (!stockAdjustLotId.value) {
        toast.add({
          title: t("components.stockAdjust.selectLotRequired"),
          color: "error",
        });
        return;
      }
      const selected = stockLotOptions.value.find((o) => o.value === stockAdjustLotId.value);
      const left = selected?.qtyRemaining ?? 0;
      if (qty > left) {
        toast.add({
          title: t("components.stockAdjust.lotQtyExceeded"),
          color: "error",
        });
        return;
      }
    }

    await productApi.adjustStock(target.id, {
      mode: stockAdjustMode.value,
      qty,
      inPrice: stockAdjustMode.value === "added" ? Number(stockAdjustInPrice.value) : 0,
      outPrice: stockAdjustMode.value === "added" ? Number(stockAdjustOutPrice.value) : 0,
      stockAdditionId:
        stockAdjustMode.value === "damaged" ? Number(stockAdjustLotId.value) : undefined,
      note: stockAdjustNote.value || undefined,
    });
    await resource.refresh();

    toast.add({
      title:
        stockAdjustMode.value === "added"
          ? t("components.stockAdjust.titleAdd")
          : t("components.stockAdjust.titleDamaged"),
      description: t("pages.product.toastStockAdjustDesc", { id: target.id }),
      color: stockAdjustMode.value === "added" ? "primary" : "warning",
    });

    isStockAdjustOpen.value = false;
    stockAdjustTarget.value = null;
    stockAdjustQty.value = 0;
    stockAdjustInPrice.value = 0;
    stockAdjustOutPrice.value = 0;
    stockAdjustNote.value = "";
    stockAdjustLotId.value = null;
    stockLotOptions.value = [];
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
      toast.add({ title: t("pages.product.toastHistoryLoadFailed"), color: "error" });
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

  async function onHistorySaved() {
    await loadHistory();
    await resource.refresh();
  }

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
    filteredEntries: effectiveEntries,
    confirmConfig,
    columns,
    entryFormFields,
    // Actions
    getDropdownActions,
    canCreate: perms.canCreate,
    canUpdate: perms.canUpdate,
    canExport: perms.canExport,
    canAdjustStock: perms.canAdjustStock,
    canViewAdjustStock: perms.canViewAdjustStock,
    canAddDamage: perms.canAddDamage,
    canViewAddDamage: perms.canViewAddDamage,
    handleSaveRequest,
    finalizeAction,
    handleAddNew,
    stockAdjustMode,
    stockAdjustQty,
    stockAdjustInPrice,
    stockAdjustOutPrice,
    stockAdjustNote,
    stockAdjustTarget,
    stockAdjustLotId,
    stockLotOptions,
    isStockLotsLoading,
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
    onHistorySaved,
  };
}
