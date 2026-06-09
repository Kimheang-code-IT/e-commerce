import { computed, ref, watch } from 'vue'
import type { DropdownMenuItem, TableColumn } from '@nuxt/ui'
import type { FormField, Supplier, SupplierProductItem } from '~/types'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import { formatCurrency } from '~/utils/format/currency'
import { useSupplierApi, type ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from '~/composables/table/useServerTableResource'
import { useMutation } from '~/composables/data/useMutation'

export function useSupplierTable() {
  const useBackendApi = useBackendMode()
  const supplierApi = useSupplierApi()
  const perms = useModulePermissions('supplier')
  const { t, toast, rowSelection, columnVisibility, isFormOpen, isConfirmOpen } = useBaseTable()
  const { sorting, columnFilters, pagination, globalFilter } = useTableQuery({
    initialSorting: [{ id: 'id', desc: false }]
  })
  const suppliers = ref<Supplier[]>([])
  const mutation = useMutation()
  const mergedServerQuery = computed(() => ({
    page: pagination.value.pageIndex + 1,
    limit: pagination.value.pageSize,
    sortBy: sorting.value[0]?.id || undefined,
    sortOrder: sorting.value[0] ? (sorting.value[0].desc ? 'desc' : 'asc') : undefined,
    search: globalFilter.value?.trim() || undefined,
  }))
  watch(globalFilter, () => {
    pagination.value.pageIndex = 0
  })
  const resource = useServerTableResource<Supplier, ApiQueryParams>({
    resourceKey: 'suppliers',
    useBackendApi,
    serverQuery: mergedServerQuery as any,
    listFn: (query, signal) => supplierApi.list(query, signal),
    localData: suppliers,
    debounceMs: 220
  })
  const effectiveSuppliers = computed(() => resource.rows.value)

  const selectedSupplier = ref<Supplier | null>(null)
  const pendingSupplier = ref<Supplier | null>(null)
  const confirmMode = ref<'add' | 'edit' | 'delete'>('add')

  const isProductsDialogOpen = ref(false)
  const supplierForProducts = ref<Supplier | null>(null)
  const supplierProducts = ref<SupplierProductItem[]>([])
  const supplierProductsLoading = ref(false)
  const supplierProductsTotal = ref(0)
  const supplierProductsDateRange = ref<{ start: any; end: any }>({ start: undefined, end: undefined })
  const isProductEditOpen = ref(false)
  const selectedProduct = ref<SupplierProductItem | null>(null)

  function toISO(val: any) {
    if (!val) return undefined
    const d = new Date(val)
    return isNaN(d.getTime()) ? undefined : d.toISOString()
  }

  async function loadSupplierProducts() {
    if (!supplierForProducts.value) return
    supplierProductsLoading.value = true
    try {
      const res = await supplierApi.listProducts(supplierForProducts.value.id, {
        page: 1,
        limit: 200,
        dateFrom: toISO(supplierProductsDateRange.value.start),
        dateTo: toISO(supplierProductsDateRange.value.end),
      })
      supplierProducts.value = (res.data || []).map((item) => ({
        ...item,
        amount: Number(item.amount || 0),
      }))
      supplierProductsTotal.value = Number(res.total || supplierProducts.value.length)
    } finally {
      supplierProductsLoading.value = false
    }
  }

  watch(
    () => [supplierProductsDateRange.value.start, supplierProductsDateRange.value.end],
    () => {
      if (isProductsDialogOpen.value && supplierForProducts.value) loadSupplierProducts()
    },
    { deep: true }
  )
  const productFormData = ref({
    id: 0,
    productName: '',
    qty: 1,
    unitPrice: 0,
    createdAt: ''
  })

  const filteredSuppliers = computed(() => effectiveSuppliers.value)
  const totalRows = computed(() => resource.totalRows.value)
  const supplierSummary = computed(() => ({
    count: totalRows.value,
    totalProducts: filteredSuppliers.value.reduce((sum, row) => sum + Number(row.totalProduct || 0), 0),
    totalAmount: filteredSuppliers.value.reduce((sum, row) => sum + Number(row.totalAmount || 0), 0)
  }))

  const columns = computed<TableColumn<Supplier>[]>(() => [
    { accessorKey: 'id', header: 'No' },
    { accessorKey: 'name', header: 'Name', footer: `Count: ${supplierSummary.value.count}` },
    { accessorKey: 'gender', header: 'Gender' },
    { accessorKey: 'address', header: 'Address' },
    { accessorKey: 'phoneNumber', header: 'Phone Number' },
    { accessorKey: 'totalProduct', header: 'Total Product', footer: supplierSummary.value.totalProducts.toLocaleString() },
    { accessorKey: 'totalAmount', header: 'Total Amount', footer: formatCurrency(supplierSummary.value.totalAmount, 'USD') },
    { id: 'action', header: t('common.actions') }
  ])

  const supplierProductsColumns = computed<TableColumn<SupplierProductItem>[]>(() => [
    { accessorKey: 'id', header: 'No' },
    { accessorKey: 'productName', header: 'Product Name' },
    { accessorKey: 'qty', header: 'Qty' },
    { accessorKey: 'unitPrice', header: 'Unit Price' },
    { accessorKey: 'amount', header: 'Amount' },
    { accessorKey: 'createdAt', header: 'Created At' }
  ]);

  const supplierFormFields = computed<FormField[]>(() => [
    { key: 'name', label: t('pages.supplier.form.name'), type: 'input', required: true, textRule: 'text' },
    {
      key: 'gender',
      label: t('pages.supplier.form.gender'),
      type: 'select',
      required: true,
      items: [
        { label: t('pages.supplier.form.genderMale'), value: 'Male' },
        { label: t('pages.supplier.form.genderFemale'), value: 'Female' },
        { label: t('pages.supplier.form.genderOther'), value: 'Other' },
      ],
    },
    { key: 'address', label: t('pages.supplier.form.address'), type: 'textarea', required: true, textRule: 'text' },
    { key: 'phoneNumber', label: t('pages.supplier.form.phoneNumber'), type: 'input', required: true, textRule: 'numeric' },
  ])
  const productFormFields = computed<FormField[]>(() => [
    { key: 'productName', label: t('pages.supplier.form.productName'), type: 'input', required: true, textRule: 'text' },
    { key: 'qty', label: t('pages.supplier.form.qty'), type: 'number', required: true, min: 1 },
    { key: 'unitPrice', label: t('pages.supplier.form.unitPrice'), type: 'currency', required: true, min: 0, currencyPrefix: 'USD' },
  ])

  const confirmConfig = computed(() => {
    if (confirmMode.value === 'delete') {
      return {
        titleKey: 'pages.supplier.confirmDeleteTitle',
        description: t('pages.supplier.confirmDeleteDesc', {
          name: selectedSupplier.value?.name || '',
        }),
        type: 'error' as const,
        submitLabelKey: 'actions.delete',
      }
    }
    if (confirmMode.value === 'edit') {
      return {
        titleKey: 'pages.supplier.confirmEditTitle',
        description: t('pages.supplier.confirmEditDesc', {
          name: pendingSupplier.value?.name || '',
        }),
        type: 'primary' as const,
        submitLabelKey: 'actions.save',
      }
    }
    return {
      titleKey: 'pages.supplier.confirmAddTitle',
      description: t('pages.supplier.confirmAddDesc', {
        name: pendingSupplier.value?.name || '',
      }),
      type: 'primary' as const,
      submitLabelKey: 'actions.confirm',
    }
  })

  function handleAddNew() {
    if (!perms.canCreate.value) return
    selectedSupplier.value = null
    isFormOpen.value = true
  }

  function handleSaveRequest(payload: Record<string, any>) {
    pendingSupplier.value = {
      id: Number(payload.id || 0),
      name: String(payload.name || '').trim(),
      gender: (String(payload.gender || 'Other') as Supplier['gender']),
      address: String(payload.address || '').trim(),
      phoneNumber: String(payload.phoneNumber || '').trim(),
      totalProduct: Number(selectedSupplier.value?.totalProduct || 0),
      totalAmount: Number(selectedSupplier.value?.totalAmount || 0),
      createdAt: selectedSupplier.value?.createdAt || new Date().toISOString()
    }
    confirmMode.value = pendingSupplier.value.id ? 'edit' : 'add'
    isConfirmOpen.value = true
  }

  async function finalizeAction() {
    if (confirmMode.value === 'delete' && selectedSupplier.value) {
      await mutation.run(() => supplierApi.remove(selectedSupplier.value!.id), 'suppliers')
      await resource.load()
      toast.add({ title: t('pages.supplier.toastDeleted'), color: 'error' })
    } else if (pendingSupplier.value) {
      if (confirmMode.value === 'add') {
        await mutation.run(
          () =>
            supplierApi.create({
              name: pendingSupplier.value!.name,
              gender: pendingSupplier.value!.gender,
              address: pendingSupplier.value!.address,
              phoneNumber: pendingSupplier.value!.phoneNumber,
            }),
          'suppliers'
        )
        await resource.load()
        toast.add({ title: t('pages.supplier.toastAdded'), color: 'primary' })
      } else {
        await mutation.run(
          () =>
            supplierApi.update(pendingSupplier.value!.id, {
              name: pendingSupplier.value!.name,
              gender: pendingSupplier.value!.gender,
              address: pendingSupplier.value!.address,
              phoneNumber: pendingSupplier.value!.phoneNumber,
            }),
          'suppliers'
        )
        await resource.load()
        toast.add({ title: t('pages.supplier.toastUpdated'), color: 'primary' })
      }
    }
    isConfirmOpen.value = false
    isFormOpen.value = false
    selectedSupplier.value = null
    pendingSupplier.value = null
  }

  function getDropdownActions(row: Supplier): DropdownMenuItem[][] {
    const items: DropdownMenuItem[] = []
    if (perms.canUpdate.value) {
      items.push({ label: t('actions.edit'), icon: 'i-lucide-pencil', onSelect: () => { selectedSupplier.value = { ...row }; isFormOpen.value = true } })
    }
    if (perms.canDelete.value) {
      items.push({ label: t('actions.delete'), icon: 'i-lucide-trash', color: 'error' as const, onSelect: () => { selectedSupplier.value = row; confirmMode.value = 'delete'; isConfirmOpen.value = true } })
    }
    return items.length ? [items] : []
  }

  async function openProductsDialog(row: Supplier) {
    supplierForProducts.value = row
    supplierProductsDateRange.value = { start: undefined, end: undefined }
    isProductsDialogOpen.value = true
    await loadSupplierProducts()
  }

  function openProductEdit(item: SupplierProductItem) {
    if (!perms.canUpdate.value) return
    selectedProduct.value = item
    productFormData.value = { id: item.id, productName: item.productName, qty: Number(item.qty || 0), unitPrice: Number(item.unitPrice || 0), createdAt: item.createdAt }
    isProductEditOpen.value = true
  }

  async function saveProductEdit(payload: Record<string, any>) {
    const supplier = supplierForProducts.value
    const product = selectedProduct.value
    if (!supplier || !product) return
    await mutation.run(
      () =>
        supplierApi.updateProduct(supplier.id, product.id, {
          productName: String(payload.productName || '').trim(),
          qty: Math.max(0, Number(payload.qty || 0)),
          unitPrice: Math.max(0, Number(payload.unitPrice || 0)),
        }),
      'suppliers'
    )
    await loadSupplierProducts()
    await resource.load()
    isProductEditOpen.value = false
    selectedProduct.value = null
    toast.add({ title: t('pages.supplier.toastProductUpdated'), color: 'primary' })
  }

  return {
    rowSelection,
    sorting,
    columnFilters,
    columnVisibility,
    pagination,
    searchQuery: globalFilter,
    suppliers: filteredSuppliers,
    totalRows,
    columns,
    supplierFormFields,
    productFormFields,
    confirmConfig,
    isFormOpen,
    isConfirmOpen,
    selectedSupplier,
    getDropdownActions,
    canCreate: perms.canCreate,
    canUpdate: perms.canUpdate,
    canView: perms.canView,
    handleSaveRequest,
    finalizeAction,
    handleAddNew,
    isProductsDialogOpen,
    supplierForProducts,
    supplierProducts,
    supplierProductsLoading,
    supplierProductsTotal,
    supplierProductsDateRange,
    supplierProductsColumns,
    openProductsDialog,
    isProductEditOpen,
    productFormData,
    openProductEdit,
    saveProductEdit
  };
}