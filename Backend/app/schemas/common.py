from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.security.input_validation import clean_optional_text, clean_string_list, clean_text


class ErrorResponse(BaseModel):
    message: str
    code: str
    traceId: str | None = None
    errors: dict[str, list[str]] | None = None


class ListQuery(BaseModel):
    page: int = 1
    limit: int = 20
    sortBy: str | None = None
    sortOrder: str | None = None
    search: str | None = Field(default=None, max_length=200)
    dateFrom: str | None = Field(default=None, max_length=40)
    dateTo: str | None = Field(default=None, max_length=40)

    @field_validator("sortBy", "sortOrder", "search", "dateFrom", "dateTo")
    @classmethod
    def normalize_optional_query_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ListResponse(BaseModel):
    data: list[dict]
    total: int
    aggregates: dict | None = None

class CategoryCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)

    @field_validator("name", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return clean_text(value)


class CategoryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)


class ProductCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=180)
    model: str = Field(default="", max_length=120)
    discountPrice: float = Field(default=0, ge=0)
    totalPrice: float = Field(default=0, ge=0)
    size: str = Field(default="", max_length=120)
    top: str = Field(default="", max_length=120)
    backSide: str = Field(default="", max_length=120)
    fretboard: str = Field(default="", max_length=180)
    string: str = Field(default="", max_length=120)
    finishing: str = Field(default="", max_length=120)
    color: str = Field(default="", max_length=120)
    categoryId: str = Field(min_length=1, max_length=40)
    supplierId: int | None = Field(default=None, ge=1)
    inPrice: float = Field(default=0, ge=0)
    outPrice: float = Field(default=0, ge=0)
    commission: float = Field(default=0, ge=0)
    totalStock: int = Field(default=0, ge=0)
    inStock: int = Field(default=0, ge=0)
    sold: int = Field(default=0, ge=0)
    added: int = Field(default=0, ge=0)
    damaged: int = Field(default=0, ge=0)
    status: str = Field(default="active", max_length=50)
    image: str | None = Field(default=None, max_length=2_500_000)
    stockNote: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "status", "model", "size", "top", "backSide", "fretboard", "string", "finishing", "color")
    @classmethod
    def normalize_product_text(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("categoryId")
    @classmethod
    def normalize_category_id(cls, value: str) -> str:
        return clean_text(value)


class StockAdditionUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qty: int | None = Field(default=None, gt=0)
    inPrice: float | None = Field(default=None, ge=0)
    outPrice: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class StockDamageUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    qty: int | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ProductStockAdjustPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = Field(pattern="^(added|damaged)$")
    qty: int = Field(gt=0)
    inPrice: float = Field(default=0, ge=0)
    outPrice: float = Field(default=0, ge=0)
    stockAdditionId: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        return clean_optional_text(value)


class ProductUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=180)
    model: str | None = Field(default=None, max_length=120)
    discountPrice: float | None = Field(default=None, ge=0)
    totalPrice: float | None = Field(default=None, ge=0)
    size: str | None = Field(default=None, max_length=120)
    top: str | None = Field(default=None, max_length=120)
    backSide: str | None = Field(default=None, max_length=120)
    fretboard: str | None = Field(default=None, max_length=180)
    string: str | None = Field(default=None, max_length=120)
    finishing: str | None = Field(default=None, max_length=120)
    color: str | None = Field(default=None, max_length=120)
    categoryId: str | None = Field(default=None, min_length=1, max_length=40)
    supplierId: int | None = Field(default=None, ge=1)
    inPrice: float | None = Field(default=None, ge=0)
    outPrice: float | None = Field(default=None, ge=0)
    commission: float | None = Field(default=None, ge=0)
    totalStock: int | None = Field(default=None, ge=0)
    inStock: int | None = Field(default=None, ge=0)
    sold: int | None = Field(default=None, ge=0)
    added: int | None = Field(default=None, ge=0)
    damaged: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=50)
    image: str | None = Field(default=None, max_length=2_500_000)
    stockNote: str | None = Field(default=None, max_length=1000)

    @field_validator("name", "status", "model", "size", "top", "backSide", "fretboard", "string", "finishing", "color")
    @classmethod
    def normalize_optional_product_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)

    @field_validator("categoryId")
    @classmethod
    def normalize_optional_category_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)


class SupplierCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=160)
    gender: str = Field(default="Other", pattern="^(Male|Female|Other)$")
    address: str = Field(default="", max_length=2000)
    phoneNumber: str = Field(default="", max_length=40)

    @field_validator("name", "address", "phoneNumber")
    @classmethod
    def normalize_supplier_text(cls, value: str) -> str:
        return clean_text(value)


class SupplierUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=160)
    gender: str | None = Field(default=None, pattern="^(Male|Female|Other)$")
    address: str | None = Field(default=None, max_length=2000)
    phoneNumber: str | None = Field(default=None, max_length=40)

    @field_validator("name", "address", "phoneNumber")
    @classmethod
    def normalize_optional_supplier_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)


class SupplierProductUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    productName: str | None = Field(default=None, min_length=1, max_length=180)
    qty: int | None = Field(default=None, ge=0)
    unitPrice: float | None = Field(default=None, ge=0)

    @field_validator("productName")
    @classmethod
    def normalize_product_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)


class InvoiceLinePayload(BaseModel):
    productId: int
    qty: int = Field(default=1, ge=1)
    unitPrice: float | None = Field(default=None, ge=0)


class PosCheckoutPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customerName: str = Field(default="", max_length=160)
    customerPhone: str = Field(default="", max_length=40)
    customerAddress: str = Field(default="", max_length=2000)
    source: str = Field(default="other", max_length=50)
    deliveryType: str = Field(default="delivery", max_length=50)
    deliveryPrice: float = Field(default=0, ge=0)
    deliveryDate: str = Field(default="", max_length=40)
    discountAmount: float = Field(default=0, ge=0)
    paymentMethod: str = Field(default="cash", max_length=50)
    deliveryStatus: str = Field(default="pending", max_length=50)
    sellerId: int | None = None
    lines: list[InvoiceLinePayload] = Field(default_factory=list, max_length=200)

    @field_validator("customerName", "customerPhone", "customerAddress", "source", "deliveryType", "deliveryDate", "paymentMethod", "deliveryStatus")
    @classmethod
    def normalize_checkout_text(cls, value: str) -> str:
        return clean_text(value)


class RefundRecordCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int | None = Field(default=None, ge=1)
    invoiceId: int | None = Field(default=None, ge=1)
    invoiceNo: str = Field(min_length=1, max_length=120)
    date: str = Field(default="", max_length=50)
    product: str = Field(min_length=1, max_length=180)
    productId: int | None = Field(default=None, ge=0)
    qty: int = Field(default=0, ge=0)
    price: float = Field(default=0, ge=0)
    customer: str = Field(default="", max_length=160)
    phoneCustomer: str = Field(default="", max_length=40)
    seller: str = Field(default="", max_length=120)
    phoneSaler: str = Field(default="", max_length=40)
    source: str = Field(default="", max_length=50)
    address: str = Field(default="", max_length=2000)
    deliveryPrice: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)
    amount: float = Field(ge=0)
    refundReason: str | None = Field(default=None, max_length=2000)

    @field_validator("productId", "qty", "price", "deliveryPrice", "discount", "amount", mode="before")
    @classmethod
    def coerce_null_numeric(cls, value):
        if value is None:
            return 0
        return value

    @field_validator("invoiceNo", "product", "customer", "phoneCustomer", "seller", "phoneSaler", "source", "address", "date")
    @classmethod
    def normalize_refund_text(cls, value: str) -> str:
        return clean_text(value)


class RefundCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[RefundRecordCreatePayload] = Field(default_factory=list, min_length=1)


class DeliveryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deliveryStatus: str = Field(min_length=1, max_length=50)

    @field_validator("deliveryStatus")
    @classmethod
    def normalize_delivery_status(cls, value: str) -> str:
        return clean_text(value)


class SystemUserCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=180)
    password: str = Field(min_length=8, max_length=255)
    role: str = Field(default="admin", min_length=1, max_length=120)
    permissions: str | None = None

    @field_validator("name", "role")
    @classmethod
    def normalize_user_text(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("email")
    @classmethod
    def normalize_user_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class SystemUserUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = Field(default=None, max_length=180)
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role: str | None = Field(default=None, min_length=1, max_length=120)
    permissions: str | None = None

    @field_validator("name", "role")
    @classmethod
    def normalize_optional_user_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)

    @field_validator("email")
    @classmethod
    def normalize_optional_user_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return None
        return str(value).lower()


class SystemRoleCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    pageAccess: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("pageAccess")
    @classmethod
    def normalize_page_access(cls, value: list[str]) -> list[str]:
        return clean_string_list(value)


class SystemRoleUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    pageAccess: list[str] | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_role_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return clean_text(value)

    @field_validator("pageAccess")
    @classmethod
    def normalize_optional_page_access(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return clean_string_list(value)


class SetupBootstrapPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=180)
    password: str = Field(min_length=8, max_length=255)
    passwordConfirm: str = Field(min_length=8, max_length=255)

    @field_validator("name")
    @classmethod
    def normalize_setup_name(cls, value: str) -> str:
        return clean_text(value)

    @field_validator("email")
    @classmethod
    def normalize_setup_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @model_validator(mode="after")
    def passwords_match(self) -> "SetupBootstrapPayload":
        if self.password != self.passwordConfirm:
            raise ValueError("Passwords do not match")
        return self


class AuthLoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=180)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class AuthUserPayload(BaseModel):
    id: int
    name: str
    email: str
    avatar: str = ""
    role: str = ""
    pageAccess: list[str] = Field(default_factory=list)


class AuthLoginData(BaseModel):
    token: str
    refreshToken: str
    user: AuthUserPayload


class AuthLoginResponse(BaseModel):
    success: bool = True
    message: str = "Login successful"
    data: AuthLoginData


class PosPreviewSessionCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoices: list[dict] = Field(default_factory=list, max_length=100)
