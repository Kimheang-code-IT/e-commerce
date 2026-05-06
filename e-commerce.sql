-- =====================================================
-- E-commerce schema (PostgreSQL)
--
-- Tables only (no extra entities in this file):
--   categories, products, product_stock_additions, product_damages,
--   roles, users, invoices, checkout_items, finances, histories
--
-- Read-only views (joins / aggregates):
--   products_view, reports_view, deliveries_view, commission_view, finance_view
-- =====================================================

-- =====================================================
-- REAL TABLES
-- =====================================================

CREATE TABLE "categories" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(120) NOT NULL UNIQUE,
    "description" TEXT NOT NULL DEFAULT '',
    "product_count" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "categories_name_index" ON "categories" ("name");
CREATE INDEX "categories_created_at_index" ON "categories" ("created_at");


CREATE TABLE "products" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(180) NOT NULL,
    "image" VARCHAR(255) NOT NULL DEFAULT '',
    "category_id" INTEGER NULL,
    "in_price" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "out_price" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "commission" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "total_stock" INTEGER NOT NULL DEFAULT 0,
    "in_stock" INTEGER NOT NULL DEFAULT 0,
    "sold" INTEGER NOT NULL DEFAULT 0,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "products_category_id_foreign" FOREIGN KEY ("category_id") REFERENCES "categories" ("id")
);

CREATE INDEX "products_name_index" ON "products" ("name");
CREATE INDEX "products_category_id_index" ON "products" ("category_id");
CREATE INDEX "products_status_index" ON "products" ("status");
CREATE INDEX "products_created_at_index" ON "products" ("created_at");


-- =====================================================
-- STOCK ADDITION HISTORY
-- =====================================================

CREATE TABLE "product_stock_additions" (
    "id" SERIAL PRIMARY KEY,
    "product_id" INTEGER NOT NULL,
    "product_name" VARCHAR(180) NOT NULL,
    "qty" INTEGER NOT NULL,
    "note" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "product_stock_additions_product_id_foreign" FOREIGN KEY ("product_id") REFERENCES "products" ("id")
);

CREATE INDEX "product_stock_additions_product_id_index" ON "product_stock_additions" ("product_id");
CREATE INDEX "product_stock_additions_created_at_index" ON "product_stock_additions" ("created_at");
CREATE INDEX "product_stock_additions_product_created_index" ON "product_stock_additions" ("product_id", "created_at");


-- =====================================================
-- DAMAGED STOCK HISTORY
-- =====================================================

CREATE TABLE "product_damages" (
    "id" SERIAL PRIMARY KEY,
    "product_id" INTEGER NOT NULL,
    "product_name" VARCHAR(180) NOT NULL,
    "qty" INTEGER NOT NULL,
    "note" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "product_damages_product_id_foreign" FOREIGN KEY ("product_id") REFERENCES "products" ("id")
);

CREATE INDEX "product_damages_product_id_index" ON "product_damages" ("product_id");
CREATE INDEX "product_damages_created_at_index" ON "product_damages" ("created_at");
CREATE INDEX "product_damages_product_created_index" ON "product_damages" ("product_id", "created_at");


CREATE TABLE "roles" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(120) NOT NULL UNIQUE,
    "page_access" TEXT NOT NULL DEFAULT '[]',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "roles_name_index" ON "roles" ("name");
CREATE INDEX "roles_created_at_index" ON "roles" ("created_at");


CREATE TABLE "users" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR(120) NOT NULL,
    "role_id" INTEGER NOT NULL,
    "email" VARCHAR(180) NOT NULL UNIQUE,
    "password_hash" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "users_role_id_foreign" FOREIGN KEY ("role_id") REFERENCES "roles" ("id")
);

CREATE INDEX "users_role_id_index" ON "users" ("role_id");
CREATE INDEX "users_email_index" ON "users" ("email");
CREATE INDEX "users_created_at_index" ON "users" ("created_at");


CREATE TABLE "invoices" (
    "id" SERIAL PRIMARY KEY,
    "invoice_no" VARCHAR(120) NOT NULL UNIQUE,
    -- This user must be seller role.
    -- Validate seller role in FastAPI when creating invoice.
    "user_id" INTEGER NOT NULL,
    "customer_name" VARCHAR(120) NOT NULL DEFAULT '',
    "customer_phone" VARCHAR(50) NOT NULL DEFAULT '',
    "customer_address" TEXT NOT NULL DEFAULT '',
    "delivery_type" VARCHAR(50) NOT NULL DEFAULT '',
    "delivery_price" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "delivery_status" VARCHAR(50) NOT NULL DEFAULT 'pending',
    "subtotal" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "discount" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "total" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "source" VARCHAR(50) NOT NULL DEFAULT 'pos',
    "payment_method" VARCHAR(50) NOT NULL DEFAULT 'cash',
    "status" VARCHAR(50) NOT NULL DEFAULT 'paid',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "invoices_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE INDEX "invoices_invoice_no_index" ON "invoices" ("invoice_no");
CREATE INDEX "invoices_user_id_index" ON "invoices" ("user_id");
CREATE INDEX "invoices_customer_name_index" ON "invoices" ("customer_name");
CREATE INDEX "invoices_delivery_type_index" ON "invoices" ("delivery_type");
CREATE INDEX "invoices_delivery_status_index" ON "invoices" ("delivery_status");
CREATE INDEX "invoices_status_index" ON "invoices" ("status");
CREATE INDEX "invoices_created_at_index" ON "invoices" ("created_at");
CREATE INDEX "invoices_status_created_index" ON "invoices" ("status", "created_at");


CREATE TABLE "checkout_items" (
    "id" SERIAL PRIMARY KEY,
    "invoice_id" INTEGER NOT NULL,
    "product_id" INTEGER NULL,
    "product_name" VARCHAR(180) NOT NULL,
    "quantity" INTEGER NOT NULL DEFAULT 1,
    "price" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "total" DECIMAL(12, 2) NOT NULL DEFAULT 0,

    CONSTRAINT "checkout_items_invoice_id_foreign" FOREIGN KEY ("invoice_id") REFERENCES "invoices" ("id"),
    CONSTRAINT "checkout_items_product_id_foreign" FOREIGN KEY ("product_id") REFERENCES "products" ("id")
);

CREATE INDEX "checkout_items_invoice_id_index" ON "checkout_items" ("invoice_id");
CREATE INDEX "checkout_items_product_id_index" ON "checkout_items" ("product_id");
CREATE INDEX "checkout_items_product_name_index" ON "checkout_items" ("product_name");
CREATE INDEX "checkout_items_product_invoice_index" ON "checkout_items" ("product_id", "invoice_id");


CREATE TABLE "finances" (
    "id" SERIAL PRIMARY KEY,
    "product_id" INTEGER NOT NULL,
    "total_commission" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "facebook" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "other" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "total_sold_product" DECIMAL(12, 2) NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "finances_product_id_foreign" FOREIGN KEY ("product_id") REFERENCES "products" ("id")
);

CREATE INDEX "finances_product_id_index" ON "finances" ("product_id");
CREATE INDEX "finances_created_at_index" ON "finances" ("created_at");
CREATE INDEX "finances_product_created_index" ON "finances" ("product_id", "created_at");


CREATE TABLE "histories" (
    "id" SERIAL PRIMARY KEY,
    "type_action" VARCHAR(120) NOT NULL,
    "user_id" INTEGER NOT NULL,
    "description" TEXT NOT NULL DEFAULT '',
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "histories_user_id_foreign" FOREIGN KEY ("user_id") REFERENCES "users" ("id")
);

CREATE INDEX "histories_type_action_index" ON "histories" ("type_action");
CREATE INDEX "histories_user_id_index" ON "histories" ("user_id");
CREATE INDEX "histories_created_at_index" ON "histories" ("created_at");
CREATE INDEX "histories_user_created_index" ON "histories" ("user_id", "created_at");


-- =====================================================
-- VIEWS
-- =====================================================

CREATE OR REPLACE VIEW "products_view" AS
SELECT
    p."id" AS "id",
    p."name" AS "name",
    p."image" AS "image",
    p."category_id" AS "category_id",
    c."name" AS "category",
    p."in_price" AS "in_price",
    p."out_price" AS "out_price",
    p."commission" AS "commission",
    p."total_stock" AS "total_stock",
    p."in_stock" AS "in_stock",
    p."sold" AS "sold",
    COALESCE(sa."added", 0) AS "added",
    COALESCE(pd."damaged", 0) AS "damaged",
    p."status" AS "status",
    p."created_at" AS "created_at"
FROM "products" p
LEFT JOIN "categories" c
    ON c."id" = p."category_id"
LEFT JOIN (
    SELECT
        "product_id",
        SUM("qty") AS "added"
    FROM "product_stock_additions"
    GROUP BY "product_id"
) sa
    ON sa."product_id" = p."id"
LEFT JOIN (
    SELECT
        "product_id",
        SUM("qty") AS "damaged"
    FROM "product_damages"
    GROUP BY "product_id"
) pd
    ON pd."product_id" = p."id";


CREATE OR REPLACE VIEW "reports_view" AS
SELECT
    ci."id" AS "id",
    i."invoice_no" AS "invoice_no",
    ci."product_id" AS "product_id",
    ci."product_name" AS "product_name",
    i."customer_name" AS "customer_name",
    i."customer_phone" AS "customer_phone",
    i."customer_address" AS "customer_address",
    i."source" AS "source",
    ci."total" AS "total_price",
    i."payment_method" AS "payment_method",
    i."status" AS "status",
    i."created_at" AS "created_at"
FROM "checkout_items" ci
JOIN "invoices" i
    ON i."id" = ci."invoice_id";


CREATE OR REPLACE VIEW "deliveries_view" AS
SELECT
    i."id" AS "id",
    i."invoice_no" AS "invoice_no",
    i."customer_name" AS "customer_name",
    i."customer_phone" AS "customer_phone",
    i."customer_address" AS "customer_address",
    i."delivery_type" AS "delivery_type",
    i."delivery_price" AS "delivery_price",
    i."delivery_status" AS "delivery_status",
    i."payment_method" AS "payment_method",
    i."status" AS "status",
    i."created_at" AS "created_at"
FROM "invoices" i;


CREATE OR REPLACE VIEW "commission_view" AS
SELECT
    ci."id" AS "id",
    u."id" AS "user_id",
    u."name" AS "seller",
    ci."product_name" AS "product_name",
    i."customer_name" AS "customer_name",
    ci."total" AS "amount",
    i."source" AS "source",
    (p."commission" * ci."quantity") AS "commission",
    i."created_at" AS "created_at"
FROM "checkout_items" ci
JOIN "invoices" i
    ON i."id" = ci."invoice_id"
LEFT JOIN "products" p
    ON p."id" = ci."product_id"
LEFT JOIN "users" u
    ON u."id" = i."user_id"
LEFT JOIN "roles" r
    ON r."id" = u."role_id"
WHERE i."status" = 'paid'
  AND LOWER(r."name") = 'seller';


CREATE OR REPLACE VIEW "finance_view" AS
SELECT
    f."id" AS "id",
    p."id" AS "product_id",
    p."name" AS "product_name",
    p."in_price" AS "in_price",
    f."total_commission" AS "total_commission",
    f."facebook" AS "facebook",
    f."other" AS "other",
    f."total_sold_product" AS "total_sold_product",
    (p."in_price" * f."total_sold_product") AS "in_price_for_pos",
    (
        f."total_sold_product"
        - f."total_commission"
        - f."facebook"
        - f."other"
        - (p."in_price" * f."total_sold_product")
    ) AS "final_price",
    f."created_at" AS "created_at"
FROM "finances" f
JOIN "products" p
    ON p."id" = f."product_id";