import { onMounted, ref } from 'vue'
import type { Reward } from '~/types'
import { useRewardApi } from '~/utils/api'

export const POS_REWARDS_TAB = '__rewards__'

export function usePosRewards() {
  const rewardApi = useRewardApi()
  const rewards = ref<Reward[]>([])
  const isLoadingRewards = ref(false)

  async function loadRewards() {
    isLoadingRewards.value = true
    try {
      const res = await rewardApi.listForPos()
      rewards.value = res?.data || []
    } finally {
      isLoadingRewards.value = false
    }
  }

  onMounted(() => {
    void loadRewards()
  })

  return {
    rewards,
    isLoadingRewards,
    loadRewards,
  }
}
