import type { CourseCardItem } from '~/components/common/CourseCard.vue'
import { courses } from '~~/config/courses'

export async function useCourseItems() {
  const { getFirstLessonPath } = await useLearningCourses()

  const courseItems = computed<CourseCardItem[]>(() => {
    return courses.map((course) => {
      return {
        id: course.id,
        category: course.category,
        bannerTitle: course.shortTitle,
        bannerSubtitle: course.description,
        studentCount: course.studentCount,
        image: course.image,
        courseTitle: course.title,
        instructorName: course.instructorName,
        lectureCount: course.lectureCount,
        price: course.price,
        originalPrice: course.originalPrice,
        isFree: course.isFree,
        to: getFirstLessonPath(course)
      }
    })
  })

  return { courseItems }
}
