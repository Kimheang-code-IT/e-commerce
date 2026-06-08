export function useMyCourses() {
  const myCoursesStore = useCookie<Record<string, string[]>>('my-courses', {
    default: () => ({}),
    maxAge: 60 * 60 * 24 * 365
  })

  const user = useCookie<{ phone?: string; email?: string } | null>('auth-user')

  const userKey = computed(() => user.value?.phone ?? user.value?.email ?? '')

  const purchasedIds = computed(() => {
    const key = userKey.value

    if (!key) {
      return []
    }

    return myCoursesStore.value[key] ?? []
  })

  function purchaseCourse(courseId: string) {
    const key = userKey.value

    if (!key || purchasedIds.value.includes(courseId)) {
      return
    }

    myCoursesStore.value = {
      ...myCoursesStore.value,
      [key]: [...purchasedIds.value, courseId]
    }
  }

  function hasPurchased(courseId?: string) {
    if (!courseId) {
      return false
    }

    return purchasedIds.value.includes(courseId)
  }

  return {
    purchasedIds,
    purchaseCourse,
    hasPurchased
  }
}
