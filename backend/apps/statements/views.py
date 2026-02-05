from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import logging

from .models import MerchantStatement, StatementData
from .serializers import (
    MerchantStatementSerializer,
    FileUploadSerializer,
    ManualEntrySerializer,
    StatementDataSerializer
)
from .services import StatementProcessingService

logger = logging.getLogger(__name__)


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

        # Process the PDF immediately (synchronous for now)
        # TODO: Move to async task queue (Celery) for production
        try:
            success = StatementProcessingService.process_uploaded_statement(statement)

            # Refresh from database to get updated data
            statement.refresh_from_db()

            response_data = {
                'message': 'File uploaded and processed successfully' if success else 'File uploaded but processing failed',
                'statement_id': statement.id,
                'file_name': statement.file_name,
                'status': statement.status,
                'processor': statement.processor_name,
                'merchant_name': statement.merchant_name,
                'statement_period_start': str(statement.statement_period_start) if statement.statement_period_start else None,
                'statement_period_end': str(statement.statement_period_end) if statement.statement_period_end else None,
                'extraction_confidence': float(statement.extraction_confidence) if statement.extraction_confidence else 0,
                'requires_review': statement.requires_review,
            }

            # Add extracted financial data if available
            if success and hasattr(statement, 'data'):
                data_serializer = StatementDataSerializer(statement.data)
                response_data['extracted_data'] = data_serializer.data

            if not success:
                response_data['extraction_notes'] = statement.extraction_notes

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error processing statement: {str(e)}", exc_info=True)
            return Response({
                'message': 'File uploaded but processing failed',
                'statement_id': statement.id,
                'error': str(e)
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
