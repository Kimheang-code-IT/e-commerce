import type { LearningNavigationItem } from '~/types/navigation'
import type { CourseDefinition } from '~~/config/courses'
import { courses, getCourseByContentRoot } from '~~/config/courses'

function normalizeStem(stem: string) {
  return stem.replace(/\\/g, '/')
}

function getContentRootFromStem(stem?: string) {
  return normalizeStem(stem ?? '').split('/')[0] ?? ''
}

function sortLessonsByStem<T extends { stem?: string }>(items: T[]) {
  return items.slice().sort((a, b) => normalizeStem(a.stem ?? '').localeCompare(normalizeStem(b.stem ?? '')))
}

export async function useLearningCourses() {
  const { data: coursePages } = await useAsyncData('learning-course-pages', async () => {
    const pages = await queryCollection('docs')
      .select('title', 'path', 'stem', 'description', 'course', 'chapter', 'lessonOrder')
      .all()

    return sortLessonsByStem(pages)
  })

  const pages = computed(() => coursePages.value ?? [])

  function getPagesForCourse(course: CourseDefinition) {
    return pages.value.filter(page => getContentRootFromStem(page.stem).toLowerCase() === course.contentRoot.toLowerCase())
  }

  function getFirstLessonPath(course: CourseDefinition) {
    return getPagesForCourse(course)[0]?.path ?? `/${course.contentRoot}`
  }

  function getCourseForPageStem(stem?: string) {
    return getCourseByContentRoot(getContentRootFromStem(stem))
  }

  function getSidebarNavigation(course: CourseDefinition | undefined): LearningNavigationItem[] {
    if (!course) {
      return []
    }

    const groups = new Map<string, LearningNavigationItem[]>()

    for (const page of getPagesForCourse(course)) {
      const chapter = page.chapter ?? 'Lessons'
      const children = groups.get(chapter) ?? []

      children.push({
        title: page.title,
        path: page.path
      })

      groups.set(chapter, children)
    }

    return Array.from(groups.entries()).map(([title, children]) => ({
      title,
      children
    }))
  }

  const courseNavItems = computed(() => {
    return courses.map(course => ({
      label: course.shortTitle,
      slug: course.slug,
      to: getFirstLessonPath(course),
      description: course.description
    }))
  })

  return {
    courses,
    pages,
    courseNavItems,
    getPagesForCourse,
    getFirstLessonPath,
    getCourseForPageStem,
    getSidebarNavigation
  }
}
