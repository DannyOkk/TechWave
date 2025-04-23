from .serializer import *
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework import viewsets
# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados pueden acceder a esta vista

    def get_permissions(self):
        if self.request.method in ['POST', 'PATCH', 'DELETE']:
            self.permission_classes = [IsAdminUser]  # Solo administradores pueden crear, actualizar o eliminar usuarios
        return super().get_permissions()

class CreateUserView(APIView):
    def post(self, request):
        data = request.data
        if User.is_authenticated: #esto falla
            if User.role == 'admin':
                data['role'] = request.data.get('operator', 'client')
            else:
                data['role'] = 'client'
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data['password'])  # Establece la contraseña de forma segura
            user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeRoleView(APIView):
    permission_classes = [IsAdminUser]  # Solo administradores pueden cambiar roles

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            new_role = request.data.get('role')
            if new_role in dict(User.ROLES):
                user.role = new_role
                user.save()
                return Response({"message": "Rol actualizado correctamente"}, status=status.HTTP_200_OK)
            return Response({"error": "Rol inválido"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({
                "message": "Login exitoso",
                "username": user.username,
                "role": user.role
            }, status=status.HTTP_200_OK)
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout exitoso"}, status=status.HTTP_200_OK)