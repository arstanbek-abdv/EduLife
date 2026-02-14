from unittest.mock import patch

from rest_framework.test import APITestCase
from rest_framework import status

from apps.users.models import CustomUser
from apps.courses.models import Course, Module, Task, Enrollment


class CoursePublicationTests(APITestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username="teacher1",
            email="teacher@test.com",
            password="testpass123",
            role=CustomUser.Role.TEACHER,
            first_name="T",
            last_name="One",
        )
        self.course = Course.objects.create(
            title="Test Course",
            description="Desc",
            short_description="Short",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.DRAFT,
        )

    def test_teacher_can_publish_course(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f"/api/courses/{self.course.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, Course.CourseStatus.PUBLISHED)
        self.assertIsNotNone(self.course.published_at)

    def test_publish_idempotent_when_already_published(self):
        self.course.status = Course.CourseStatus.PUBLISHED
        self.course.save()
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f"/api/courses/{self.course.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EnrollmentTests(APITestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username="teacher2",
            email="teacher2@test.com",
            password="testpass123",
            role=CustomUser.Role.TEACHER,
            first_name="T",
            last_name="Two",
        )
        self.student = CustomUser.objects.create_user(
            username="student1",
            email="student@test.com",
            password="testpass123",
            role=CustomUser.Role.STUDENT,
            first_name="S",
            last_name="One",
        )
        self.published_course = Course.objects.create(
            title="Published",
            description="D",
            short_description="S",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.PUBLISHED,
        )
        self.draft_course = Course.objects.create(
            title="Draft",
            description="D",
            short_description="S",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.DRAFT,
        )

    def test_student_can_enroll_in_published_course(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.published_course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            Enrollment.objects.filter(
                student=self.student,
                course=self.published_course,
                status=Enrollment.Status.ACTIVE,
            ).exists()
        )

    def test_student_cannot_enroll_in_draft_course(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.draft_course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_teacher_cannot_enroll(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(f"/api/courses/{self.published_course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_double_enroll_returns_409(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.published_course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.post(f"/api/courses/{self.published_course.id}/enroll/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class CourseAccessTests(APITestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username="teacher3",
            email="teacher3@test.com",
            password="testpass123",
            role=CustomUser.Role.TEACHER,
            first_name="T",
            last_name="Three",
        )
        self.student = CustomUser.objects.create_user(
            username="student2",
            email="student2@test.com",
            password="testpass123",
            role=CustomUser.Role.STUDENT,
            first_name="S",
            last_name="Two",
        )
        self.published_course = Course.objects.create(
            title="Published",
            description="D",
            short_description="S",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.PUBLISHED,
        )
        self.module = Module.objects.create(
            course=self.published_course,
            title="M1",
            description="Mod",
            order=1,
        )
        self.task = Task.objects.create(
            module=self.module,
            title="Task1",
            description="Task desc",
            task_type=Task.TaskType.VIDEO,
            file_key="tasks/1/somekey.pdf",
        )

    def test_student_sees_only_published_courses_in_list(self):
        draft = Course.objects.create(
            title="Draft",
            description="D",
            short_description="S",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.DRAFT,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [c["id"] for c in response.data.get("results", response.data)]
        self.assertIn(self.published_course.id, ids)
        self.assertNotIn(draft.id, ids)

    def test_teacher_sees_own_courses_with_enrolled_count(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get("/api/courses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get("results", response.data)
        self.assertGreaterEqual(len(data), 1)
        self.assertIn("enrolled_count", data[0])

    def test_unenrolled_student_gets_outline_on_retrieve(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/courses/{self.published_course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        modules = response.data.get("module_to_course", [])
        if modules:
            tasks = modules[0].get("tasks", [])
            if tasks:
                # Outline: no description / external_url
                self.assertNotIn("description", tasks[0])
                self.assertNotIn("external_url", tasks[0])
                self.assertIn("id", tasks[0])
                self.assertIn("title", tasks[0])
                self.assertIn("task_type", tasks[0])

    def test_enrolled_student_gets_full_content_on_retrieve(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.published_course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get(f"/api/courses/{self.published_course.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        modules = response.data.get("module_to_course", [])
        if modules:
            tasks = modules[0].get("tasks", [])
            if tasks:
                self.assertIn("description", tasks[0])
                self.assertIn("has_file", tasks[0])


class TaskFileAccessTests(APITestCase):
    def setUp(self):
        self.teacher = CustomUser.objects.create_user(
            username="teacher4",
            email="teacher4@test.com",
            password="testpass123",
            role=CustomUser.Role.TEACHER,
            first_name="T",
            last_name="Four",
        )
        self.student = CustomUser.objects.create_user(
            username="student3",
            email="student3@test.com",
            password="testpass123",
            role=CustomUser.Role.STUDENT,
            first_name="S",
            last_name="Three",
        )
        self.course = Course.objects.create(
            title="Course",
            description="D",
            short_description="S",
            language="en",
            teacher=self.teacher,
            status=Course.CourseStatus.PUBLISHED,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="M1",
            description="Mod",
            order=1,
        )
        self.task_with_file = Task.objects.create(
            module=self.module,
            title="TaskWithFile",
            description="D",
            task_type=Task.TaskType.DOCUMENT,
            file_key="tasks/99/file.pdf",
        )
        self.task_no_file = Task.objects.create(
            module=self.module,
            title="TaskNoFile",
            description="D",
            task_type=Task.TaskType.VIDEO,
            file_key="",
        )

    def test_unenrolled_student_gets_403_on_task_file(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.get(
            f"/api/courses/tasks/{self.task_with_file.id}/file/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.courses.course_views.get_minio_client")
    def test_enrolled_student_gets_200_and_url_on_task_file(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.presigned_get_object.return_value = "https://minio.example/bucket/key"
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get(
            f"/api/courses/tasks/{self.task_with_file.id}/file/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url", response.data)

    @patch("apps.courses.course_views.get_minio_client")
    def test_teacher_owner_gets_200_on_task_file(self, mock_get_client):
        mock_client = mock_get_client.return_value
        mock_client.presigned_get_object.return_value = "https://minio.example/bucket/key"
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(
            f"/api/courses/tasks/{self.task_with_file.id}/file/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("url", response.data)

    def test_task_without_file_returns_404(self):
        Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status=Enrollment.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.student)
        response = self.client.get(
            f"/api/courses/tasks/{self.task_no_file.id}/file/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
