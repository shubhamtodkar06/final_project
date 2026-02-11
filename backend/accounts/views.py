# backend/accounts/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer, UserSerializer
from .models import StudentProfile

from student_notes.models import Standard, Subject, Topic
from progress.models import StudentTopicProgress


# ======================================================
# AUTH
# ======================================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ======================================================
# STUDENT PROFILE + LEARNING PATH INITIALIZATION
# ======================================================

class StudentProfileSetupView(APIView):
    """
    - Creates or updates student profile
    - Initializes topic-level progress
    - Ensures ONLY first topic is available
    - Locks all remaining topics
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        grade = request.data.get("grade")
        board = request.data.get("board")

        if not grade:
            return Response(
                {"error": "grade is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -----------------------------
        # CREATE / UPDATE PROFILE
        # -----------------------------
        profile, created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={"grade": grade, "board": board}
        )

        if not created:
            profile.grade = grade
            profile.board = board
            profile.save()

        # -----------------------------
        # INITIALIZE TOPIC PROGRESS
        # -----------------------------
        try:
            standard = Standard.objects.get(grade=profile.grade)
            subjects = Subject.objects.filter(standard=standard)

            for subject in subjects:
                topics = Topic.objects.filter(
                    subject=subject
                ).order_by("order_index")

                for index, topic in enumerate(topics):
                    progress, created = StudentTopicProgress.objects.get_or_create(
                        student=user,
                        topic=topic,
                        defaults={
                            "status": "available" if index == 0 else "locked"
                        }
                    )

                    # 🔴 CRITICAL: update existing rows
                    if not created:
                        expected_status = "available" if index == 0 else "locked"
                        if progress.status != expected_status:
                            progress.status = expected_status
                            progress.save()

        except Exception as e:
            print("Topic unlock failed:", e)

        return Response(
            {
                "message": "Student profile saved successfully",
                "profile": {
                    "grade": profile.grade,
                    "board": profile.board
                }
            },
            status=status.HTTP_200_OK
        )