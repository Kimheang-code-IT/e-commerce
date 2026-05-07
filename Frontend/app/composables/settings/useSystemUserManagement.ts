import { ref, computed, watch, onMounted } from "vue";
import type { TableColumn, DropdownMenuItem } from "@nuxt/ui";
import { useBaseTable } from "~/composables/table/useBaseTable";
import { useTableQuery } from "~/composables/table/useTableQuery";
import type { SystemUser, FormField } from "~/types";
import { useSystemUserApi } from '~/utils/api'
import { useSystemRoleApi } from '~/utils/api'
import type { ApiQueryParams } from '~/utils/api'
import { useServerTableResource } from "~/composables/table/useServerTableResource";
import { useMutation } from "~/composables/data/useMutation";

export function useSystemUserManagement() {
  const useBackendApi = useBackendMode()
  const systemUserApi = useSystemUserApi()
  const systemRoleApi = useSystemRoleApi()
  const { formattedRange } = useGlobalFilter()
  const {
    t, toast, rowSelection, columnVisibility,
    isFormOpen, isConfirmOpen
  } = useBaseTable({
    initialVisibility: { password: false }
  });

  const {
    sorting, columnFilters, pagination, serverQuery
  } = useTableQuery({ initialSorting: [{ id: "id", desc: false }] });
  const searchQuery = ref("")

  // --- Context States ---
  const selectedUser = ref<SystemUser | null>(null);
  const pendingUser = ref<SystemUser | null>(null);
  const confirmMode = ref<"add" | "edit" | "delete">("add");

  // --- Mock Data ---
  const users = ref<SystemUser[]>([]);
  const mutation = useMutation()
  const mergedServerQuery = computed(() => ({
    ...serverQuery.value,
    search: searchQuery.value.trim() || undefined,
    dateFrom: formattedRange.value.start || undefined,
    dateTo: formattedRange.value.end || undefined,
  }))
  watch(searchQuery, () => {
    pagination.value.pageIndex = 0
  })
  const resource = useServerTableResource<SystemUser, ApiQueryParams>({
    resourceKey: 'users',
    useBackendApi,
    serverQuery: mergedServerQuery,
    localData: users,
    listFn: (query, signal) => systemUserApi.list(query, signal),
    debounceMs: 220
  })
  const effectiveUsers = computed(() => resource.rows.value)

  // --- Filter States ---
  const roleItems = ref<string[]>([])
  const selectedRoles = ref<string[]>([]);
  async function loadRoleItems() {
    try {
      const res = await systemRoleApi.list({ page: 1, limit: 200, sortBy: 'name', sortOrder: 'asc' })
      roleItems.value = (res.data || []).map((r: any) => String(r?.name || '').trim()).filter(Boolean)
    } catch {
      roleItems.value = []
    }
  }
  onMounted(loadRoleItems)

  // --- Computed Logic ---
  const filteredUsers = computed(() => {
    if (selectedRoles.value.length === 0) return effectiveUsers.value;
    return effectiveUsers.value.filter((u) => selectedRoles.value.includes(u.role));
  });

  const userSummary = computed(() => ({
    count: filteredUsers.value.length
  }));

  const confirmConfig = computed(() => {
    if (confirmMode.value === "delete") {
      return {
        title: t("actions.delete"),
        description: `Confirm permanent removal of account for "${selectedUser.value?.name || ""}"?`,
        type: "error" as const,
        submitLabel: t("actions.delete"),
        icon: "i-lucide-user-minus",
      };
    }
    if (confirmMode.value === "edit") {
      return {
        title: t("actions.save"),
        description: `Confirm updating account for "${pendingUser.value?.name || ""}"?`,
        submitLabel: t("actions.save"),
        type: "primary" as const,
        icon: "i-lucide-user-check",
      }
    }
    return {
      title: t("pages.userManagement.addBtn"),
      description: `Confirm creating a new account for "${pendingUser.value?.name || ""}"?`,
      submitLabel: t("actions.confirm"),
      type: "primary" as const,
      icon: "i-lucide-user-plus",
    };
  });

  // --- Table Columns (Translated & Reactive) ---
  const columns = computed<TableColumn<SystemUser>[]>(() => [
    { accessorKey: "id", header: t("common.rank") },
    {
      accessorKey: "name",
      header: t("pages.userManagement.columns.name"),
      footer: `Count: ${userSummary.value.count}`
    },
    { accessorKey: "role", header: t("pages.userManagement.columns.role") },
    { accessorKey: "email", header: t("pages.userManagement.columns.email") },
    {
      accessorKey: "password",
      header: t("pages.userManagement.columns.password"),
    },
    {
      accessorKey: "lastLogin",
      header: t("pages.userManagement.columns.lastLogin"),
    },
    { id: "action", header: t("common.actions") },
  ]);

  // --- Form Fields ---
  const userFormFields = computed<FormField[]>(() => [
    {
      key: "name",
      label: t("pages.userManagement.columns.name"),
      type: "input",
      icon: "i-lucide-user",
      required: true,
    },
    {
      key: "role",
      label: t("pages.userManagement.columns.role"),
      type: "select",
      items: roleItems.value,
      icon: "i-lucide-shield-half",
      required: true,
    },
    {
      key: "email",
      label: t("pages.userManagement.columns.email"),
      type: "input",
      icon: "i-lucide-mail",
      required: true,
    },
    {
      key: "password",
      label: t("pages.userManagement.columns.password"),
      type: "password",
      icon: "i-lucide-lock",
      placeholder: "Min 8 chars...",
      showIfEdit: false,
    }
  ]);

  // --- Actions ---
  function getDropdownActions(user: SystemUser): DropdownMenuItem[][] {
    return [
      [
        {
          label: t("actions.edit"),
          icon: "i-lucide-edit",
          onSelect: () => {
            selectedUser.value = { ...user };
            isFormOpen.value = true;
          },
        },
        {
          label: t("actions.delete"),
          icon: "i-lucide-trash",
          color: "error" as const,
          onSelect: () => {
            selectedUser.value = user;
            confirmMode.value = "delete";
            isConfirmOpen.value = true;
          },
        },
      ],
    ];
  }

  function handleSaveRequest(data: SystemUser) {
    pendingUser.value = { ...data };
    confirmMode.value = (pendingUser.value.id === 0 || !pendingUser.value.id) ? "add" : "edit";
    isConfirmOpen.value = true;
  }

  async function finalizeAction() {
    if (confirmMode.value === "delete" && selectedUser.value) {
      await mutation.run(() => systemUserApi.remove(selectedUser.value!.id), 'users')
      await resource.refresh()
      toast.add({
        title: "Account Revoked",
        description: `Access revoked for ${selectedUser.value.name}.`,
        color: "error",
      });
    } else if (pendingUser.value) {
      if (confirmMode.value === "add") {
        await mutation.run(() => systemUserApi.create(pendingUser.value!), 'users')
        await resource.refresh()
        toast.add({
          title: "Account Provisioned",
          description: "System credentials delivered.",
          color: "primary",
        });
      } else if (confirmMode.value === "edit") {
        const { id, lastLogin, commission, ...updatePayload } = pendingUser.value!
        if (!updatePayload.password) delete updatePayload.password
        
        await mutation.run(() => systemUserApi.update(id, updatePayload), 'users')
        await resource.refresh()
        toast.add({
          title: "Account Synchronized",
          description: "Profile changes applied successfully.",
          color: "primary",
        });
      }
    }
    isConfirmOpen.value = false;
    isFormOpen.value = false;
    selectedUser.value = null;
    pendingUser.value = null;
  }

  function handleAddNew() {
    selectedUser.value = null;
    isFormOpen.value = true;
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
    isFormOpen,
    isConfirmOpen,
    selectedUser,
    users: effectiveUsers,
    totalRows: resource.totalRows,
    isLoading: resource.isLoading,
    roleItems,
    selectedRoles,
    // Computed
    filteredUsers,
    confirmConfig,
    // Config
    columns,
    userFormFields,
    // Actions
    getDropdownActions,
    handleSaveRequest,
    finalizeAction,
    handleAddNew,
  };
}

