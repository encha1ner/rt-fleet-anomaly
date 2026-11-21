from fastapi import HTTPException, status


class AppException:

    @staticmethod
    def invalid_credentials():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def unauthorized():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @staticmethod
    def forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    @staticmethod
    def time_valid():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start time is invalid"
        )

    @staticmethod
    def vehicle_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle Not Found"
        )

    @staticmethod
    def user_already_exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    @staticmethod
    def medicine_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found"
        )

    @staticmethod
    def supplier_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )

    @staticmethod
    def customer_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )

    @staticmethod
    def order_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    @staticmethod
    def inventory_not_found():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found"
        )

    @staticmethod
    def insufficient_stock():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient stock available"
        )

    @staticmethod
    def expired_medicine():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medicine has expired"
        )

    @staticmethod
    def duplicate_medicine():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Medicine already exists"
        )

    @staticmethod
    def validation_error(message: str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    @staticmethod
    def server_error():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not working"
        )

    