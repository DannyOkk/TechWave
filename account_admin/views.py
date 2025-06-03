from .serializer import *
from .models import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from TechWave.permissions import *

# Create your views here.
class CreateUserView(APIView):

    def post(self, request):
        data = request.data.copy()  # Crear copia mutable para evitar errores
        
        # Si el usuario está autenticado, mantener lógica de roles
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            if user.role not in ['admin', 'operator']:
                return Response(
                    {"error": "No tienes permiso para crear usuarios."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Admin puede asignar cualquier rol, operator solo client
            if user.role == 'admin':
                data['role'] = data.get('role', 'client')
            else:
                data['role'] = 'client'
        else:
            # Usuario no autenticado: solo puede crear clientes
            data['role'] = 'client'
        
        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            new_user = serializer.save()
            new_user.set_password(request.data['password'])
            new_user.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangeRoleView(APIView):
    permission_classes = [IsAdmin]  # Solo administradores pueden cambiar roles

    def put(self, request, user_id):
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

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # Marca el token como inválido
            return Response({"message": "Sesión cerrada correctamente"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Token inválido o ya expirado"}, status=status.HTTP_400_BAD_REQUEST)
    