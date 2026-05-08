<script setup lang="ts">
const { stats: apiStats, currentAnalytics, topProducts, userCommissions } = useAnalyticsDashboard()

// Keep dashboard charts large and balanced across screen sizes.
const SECTION_HEIGHT = {
  DASHBOARD: "clamp(560px, calc(100vh - 220px), 760px)",
};

type PieDataPoint = { name: string; value: number };
type BarDataPoint = { labels: string[]; values: number[] };

const provinceCustomerBuyData = computed<PieDataPoint[]>(() =>
  currentAnalytics.value.chartData?.length ? currentAnalytics.value.chartData : []
);

const summaryStats = computed(() => {
  if (apiStats.value?.length) return apiStats.value
  return []
});

const productBarData = computed<BarDataPoint>(() =>
  topProducts.value?.length
    ? {
        labels: topProducts.value.map((item) => item.name),
        values: topProducts.value.map((item) => Number(item.value || 0))
      }
    : { labels: [], values: [] }
);

const userSalePieData = computed<PieDataPoint[]>(() =>
  userCommissions.value?.length
    ? userCommissions.value
    : []
);
</script>
<template>
    <div class="flex flex-col h-full bg-background text-foreground tracking-tight">
      <div class="sticky top-0 z-30 bg-white dark:bg-gray-900">
        <LayoutAppHeader :title="$t('pages.dashboard.title')" show-datepicker />
      </div>

    <div class="flex-1 p-2 space-y-3">
    <!-- Top Summary Cards -->
    <UPageGrid class="grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      <template
        v-for="(stat, idx) in summaryStats"
        :key="idx"
      >
        <UCard class="shadow-sm border-accented">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-primary/10 rounded-lg">
              <UIcon
                :name="stat.icon"
                class="size-6 text-primary"
              />
            </div>
            <div class="min-w-0 flex-1">
              <p
                class="text-sm font-bold text-muted-foreground text-gray-500"
              >
                {{ stat.label }}
              </p>
              <h3
                class="text-2xl font-black tracking-tight text-foreground truncate"
              >
                {{ stat.value }}
              </h3>
            </div>
          </div>
        </UCard>
      </template>
    </UPageGrid>

    <!-- Bottom Grid: Reports and Distributions -->
    <div
      class="grid grid-cols-1 lg:grid-cols-12 gap-3 pb-4 items-stretch"
      :style="{ minHeight: SECTION_HEIGHT.DASHBOARD }"
    >
      <!-- Left: Cambodia Map (Customer Buy Analytics) -->
      <UCard
        class="lg:col-span-8 shadow-sm border-accented flex flex-col overflow-hidden"
        :style="{ minHeight: SECTION_HEIGHT.DASHBOARD }"
        :ui="{ body: 'p-0 flex-1 min-h-0' }"
      >
        <template #header>
          <div class="flex items-center gap-2">
            <UIcon
              name="i-lucide-map"
              class="size-5 text-primary"
            />
            <h2 class="font-normal text-foreground">
              {{ $t("pages.dashboard.revenueByRegion") }}
            </h2>
          </div>
        </template>
        <div
          class="w-full relative transition-all duration-300 flex-1 min-h-0"
          :style="{ opacity: 1 }"
        >
          <div
            v-if="false"
            class="absolute inset-x-0 top-10 bottom-0 flex flex-col gap-2 p-4"
          >
            <USkeleton v-for="i in 10" :key="i" class="h-4 w-full" />
          </div>
          <ChartAppChartMap
            :data="provinceCustomerBuyData"
            label="Total Units Sold"
          />
        </div>
      </UCard>

      <!-- Right: Distribution Pie & Small Bar -->
      <div
        class="lg:col-span-4 gap-3 flex flex-col min-h-0"
        :style="{ minHeight: SECTION_HEIGHT.DASHBOARD }"
      >
        <UCard
          class="shadow-sm border-accented relative min-h-0 overflow-hidden flex flex-col basis-[52%] p-0"
        >
          <template #header>
            <h3 class="font-normal text-sm">
              {{ $t('pages.dashboard.commissionDistribution') }}
            </h3>
          </template>
          <div class="w-full relative flex-1 min-h-0">
            <USkeleton
              v-if="false"
              class="absolute inset-0 m-12 rounded-full"
            />
            <ChartAppChartPie :data="userSalePieData" />
          </div>
        </UCard>

        <UCard
          class="shadow-sm border-accented relative min-h-0 overflow-hidden flex flex-col"
        >
          <template #header>
            <h3 class="font-normal text-sm">
              {{ $t('pages.dashboard.topSellingProducts') }}
            </h3>
          </template>
          <div class="w-full relative flex-1 min-h-0">
            <div
              v-if="false"
              class="absolute inset-0 flex items-end gap-2"
            >
              <USkeleton class="h-10 flex-1" />
              <USkeleton class="h-20 flex-1" />
              <USkeleton class="h-14 flex-1" />
              <USkeleton class="h-18 flex-1" />
            </div>
            <ChartAppChartBar
              :data="{
                labels: productBarData.labels,
                values: productBarData.values,
              }"
            />
          </div>
        </UCard>
      </div>
    </div>
    </div>
  </div>
</template>
