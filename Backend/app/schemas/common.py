from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    search: str | None = None
    dateFrom: str | None = None
    dateTo: str | None = None


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
        return value.strip()


class CategoryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "description")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class ProductCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=180)
    categoryId: str = Field(min_length=1, max_length=40)
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

    @field_validator("name", "status")
    @classmethod
    def normalize_product_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("categoryId")
    @classmethod
    def normalize_category_id(cls, value: str) -> str:
        return value.strip()


class ProductUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=180)
    categoryId: str | None = Field(default=None, min_length=1, max_length=40)
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

    @field_validator("name", "status")
    @classmethod
    def normalize_optional_product_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("categoryId")
    @classmethod
    def normalize_optional_category_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class InvoiceLinePayload(BaseModel):
    productId: int
    qty: int = Field(default=1, ge=1)


class PosCheckoutPayload(BaseModel):
    customerName: str = ""
    customerPhone: str = ""
    customerAddress: str = ""
    source: str = "other"
    deliveryType: str = "delivery"
    deliveryPrice: float = 0
    deliveryDate: str = ""
    discountPercent: float = 0
    paymentMethod: str = "cash"
    deliveryStatus: str = "pending"
    sellerId: int | None = None
    lines: list[InvoiceLinePayload] = Field(default_factory=list)




class SystemUserCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(default="secret123", min_length=6, max_length=255)
    role: str = Field(default="admin", min_length=1, max_length=120)
    permissions: str | None = None

    @field_validator("name", "email", "role")
    @classmethod
    def normalize_user_text(cls, value: str) -> str:
        return value.strip()


class SystemUserUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=180)
    password: str | None = Field(default=None, min_length=6, max_length=255)
    role: str | None = Field(default=None, min_length=1, max_length=120)
    permissions: str | None = None

    @field_validator("name", "email", "role")
    @classmethod
    def normalize_optional_user_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class SystemRoleCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    pageAccess: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_role_name(cls, value: str) -> str:
        return value.strip()


class SystemRoleUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    pageAccess: list[str] | None = None

    @field_validator("name")
    @classmethod
    def normalize_optional_role_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class AuthLoginPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=180)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip()


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
    invoices: list[dict] = Field(default_factory=list)
