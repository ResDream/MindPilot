from fastapi import APIRouter
from ..model_configs.model_config_api import add_model_config, list_model_configs, get_model_config, update_model_config, delete_model_config

config_router = APIRouter(prefix="/api/model_configs", tags=["模型配置"])

config_router.post(
    "/add",
    summary="创建模型配置",
)(add_model_config)

config_router.get(
    "",
    summary="查询所有模型配置",
)(list_model_configs)

config_router.get(
    "{config_id}",
    summary="查询单个配置",
)(get_model_config)

config_router.put(
    "{config_id}",
    summary="更新配置",
)(update_model_config)

config_router.delete(
    "{config_id}",
    summary="删除配置",
)(delete_model_config)