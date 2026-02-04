from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import MerchantStatement, StatementData
from .serializers import (
    MerchantStatementSerializer,
    FileUploadSerializer,
    ManualEntrySerializer,
    StatementDataSerializer
)


class FileUploadView(APIView):
    """
    API endpoint for uploading statement files (PDF/Image)
    POST /api/v1/statements/upload/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = serializer.validated_data['file']

        # Create statement record
        statement = MerchantStatement.objects.create(
            created_by=request.user,
            source='UPLOAD',
            status='PENDING',
            file=uploaded_file,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=uploaded_file.content_type
        )

        # TODO: Trigger async task for PDF extraction (Milestone 4)
        # For now, just mark as pending

        return Response({
            'message': 'File uploaded successfully',
            'statement_id': statement.id,
            'file_name': statement.file_name,
            'status': statement.status,
            'note': 'PDF extraction will be implemented in Milestone 4'
        }, status=status.HTTP_201_CREATED)


class ManualEntryView(APIView):
    """
    API endpoint for manual data entry
    POST /api/v1/statements/manual/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ManualEntrySerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        # Create statement record
        statement = MerchantStatement.objects.create(
            created_by=request.user,
            source='MANUAL',
            status='COMPLETED',
            merchant_name=data['merchant_name'],
            statement_period_start=data['period_start'],
            statement_period_end=data['period_end'],
            processed_at=timezone.now()
        )

        # Create statement data
        statement_data = StatementData.objects.create(
            statement=statement,
            total_volume=data['total_volume'],
            transaction_count=data['transaction_count'],
            interchange_fees=data.get('interchange_fees', 0),
            processing_fees=data.get('processing_fees', 0),
            monthly_fees=data.get('monthly_fees', 0),
            other_fees=data.get('other_fees', 0)
        )

        # Return response
        statement_serializer = MerchantStatementSerializer(statement)

        return Response({
            'message': 'Statement data created successfully',
            'statement': statement_serializer.data
        }, status=status.HTTP_201_CREATED)


class StatementListView(generics.ListAPIView):
    """
    API endpoint to list user's statements
    GET /api/v1/statements/
    """
    serializer_class = MerchantStatementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own statements
        # Admins can see all
        if self.request.user.role == 'ADMIN':
            return MerchantStatement.objects.all()
        return MerchantStatement.objects.filter(created_by=self.request.user)


class StatementDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get statement details
    GET /api/v1/statements/{id}/
    """
    serializer_class = MerchantStatementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own statements
        # Admins can see all
        if self.request.user.role == 'ADMIN':
            return MerchantStatement.objects.all()
        return MerchantStatement.objects.filter(created_by=self.request.user)
