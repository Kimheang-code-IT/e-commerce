from fastapi import APIRouter
from app.api.v1 import (
    auth,
    backup,
    catalog,
    categories,
    commission,
    dashboard,
    delivery,
    finance,
    history,
    pos,
    products,
    reports,
    refunds,
    rewards,
    suppliers,
    system_roles,
    system_users,
    tasks,
    telegram,
)

router = APIRouter()
router.include_router(auth.router)
router.include_router(catalog.router)
router.include_router(backup.router)
router.include_router(telegram.router)
router.include_router(categories.router)
router.include_router(products.router)
router.include_router(suppliers.router)
router.include_router(system_users.router)
router.include_router(system_roles.router)
router.include_router(finance.router)
router.include_router(reports.router)
router.include_router(refunds.router)
router.include_router(rewards.router)
router.include_router(history.router)
router.include_router(commission.router)
router.include_router(delivery.router)
router.include_router(pos.router)
router.include_router(pos.pos_router)
router.include_router(dashboard.router)
router.include_router(tasks.router)
