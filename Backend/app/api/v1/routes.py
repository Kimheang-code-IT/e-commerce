from fastapi import APIRouter

from app.api.v1 import auth, categories, comission, delivery, finance, history, pos, products, reports, system_roles, system_users

router = APIRouter()
router.include_router(auth.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(system_users.router)
router.include_router(system_roles.router)
router.include_router(finance.router)
router.include_router(reports.router)
router.include_router(history.router)
router.include_router(comission.router)
router.include_router(delivery.router)
router.include_router(pos.router)
router.include_router(pos.pos_router)
