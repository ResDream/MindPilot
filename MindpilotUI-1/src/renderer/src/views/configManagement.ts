import axios from "axios";
import { ref, reactive, computed } from "vue";
import { ElMessage } from "element-plus";

const API_BASE_URL = "http://127.0.0.1:7861/api/model_configs";

export interface ModelConfig {
  config_id?: string;
  config_name: string;
  platform: string;
  base_url: string;
  api_key: string;
  llm_model: {
    model: string;
    callbacks: boolean;
    max_tokens: number;
    temperature: number;
  };
}


export const useConfigManagement = () => {
  const isEditMode = computed(() => !!activeConfigId.value);
  const isDeleteButtonDisabled = computed(() => !activeConfigId.value);
  const configs = ref<ModelConfig[]>([]);
  const activeConfigId = ref("");
  const isShowConfigManagementDialog = ref(false);
  const configManagementForm = reactive<ModelConfig>({
    config_name: "",
    platform: "",
    base_url: "",
    api_key: "",
    llm_model: {
      model: "",
      callbacks: true,
      max_tokens: 4096,
      temperature: 1
    }
  });


  const isSaveButtonDisabled = computed(() => {
    // 如果是编辑模式，按钮总是启用的
    if (isEditMode.value) {
      return false;
    }
    // 如果是新建模式，只有当配置名称为空时才禁用按钮
    return !configManagementForm.config_name.trim();
  });

  const fetchAllConfigs = async () => {
    try {
      const response = await axios.get(API_BASE_URL);
      if (response.data.code === 200) {
        configs.value = response.data.data;
      } else {
        ElMessage.error(response.data.msg);
      }
    } catch (error) {
      ElMessage.error("无法获取配置");
      console.error("无法获取配置：", error);
    }
  };

  const fetchSingleConfig = async (configId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/${configId}`);
      if (response.data.code === 200) {
        Object.assign(configManagementForm, response.data.data);
        activeConfigId.value = configId;
      } else {
        ElMessage.error(response.data.msg);
      }
    } catch (error) {
      ElMessage.error("无法获取配置");
      console.error("无法获取配置：", error);
    }
  };

  const addNewConfig = async () => {
    try {
      const response = await axios.post(API_BASE_URL + "/add", configManagementForm);
      if (response.data.code === 200) {
        ElMessage.success("配置新建成功");
        await fetchAllConfigs();
        // isShowConfigManagementDialog.value = false;
        return response.data.data; // 返回新创建的配置
      } else {
        ElMessage.error(response.data.msg);
      }
    } catch (error) {
      ElMessage.error("添加配置失败");
      console.error("Failed to add configuration:", error);
    }
    return null;
  };
  const handleNewConfig = () => {
    activeConfigId.value = "";
    Object.assign(configManagementForm, {
      config_name: "",
      platform: "",
      base_url: "",
      api_key: "",
      llm_model: {
        model: "",
        callbacks: true,
        max_tokens: 4096,
        temperature: 1
      }
    });
  };
  if (isShowConfigManagementDialog.value) {
    // 如果对话框已经打开，更新标题
    const dialogEl = document.querySelector(".el-dialog__title");
    if (dialogEl) {
      dialogEl.textContent = "新建配置";
    }
  }

  const updateConfig = async () => {
    try {
      const response = await axios.put(`${API_BASE_URL}/${activeConfigId.value}`, configManagementForm);
      if (response.data.code === 200) {
        ElMessage.success("配置更新成功");
        await fetchAllConfigs();
        // isShowConfigManagementDialog.value = false; // 不自动关闭
      } else {
        ElMessage.error(response.data.msg);
      }
    } catch (error) {
      ElMessage.error("更新配置失败");
      console.error("Failed to update configuration:", error);
    }
  };

  const deleteConfig = async () => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/${activeConfigId.value}`);
      if (response.data.code === 200) {
        ElMessage.success("已成功删除配置");

        Object.assign(configManagementForm, {
          config_name: "",
          platform: "",
          base_url: "",
          api_key: "",
          llm_model: {
            model: "",
            callbacks: true,
            max_tokens: 4096,
            temperature: 1
          }
        });

        activeConfigId.value = "";

        await fetchAllConfigs();
        // isShowConfigManagementDialog.value = false;
      } else {
        ElMessage.error(response.data.msg);
      }
    } catch (error) {
      ElMessage.error("无法删除配置");
      console.error("Failed to delete configuration:", error);
    }
  };

  const handleSaveConfig = async () => {
    if (activeConfigId.value) {
      await updateConfig();
    } else {
      const newConfig = await addNewConfig();
      if (newConfig) {
        activeConfigId.value = newConfig.config_id.toString();
      }
    }
  };

  const handleDeleteConfig = async () => {
    if (activeConfigId.value) {
      await deleteConfig();
    } else {
      ElMessage.warning("请选择要删除的配置");
    }
  };

  const handleConfigSelect = async (configId) => {
    await fetchSingleConfig(configId);
    // 可以考虑添加一个小延迟，确保 activeConfigId 已经更新
    setTimeout(() => {
      if (isShowConfigManagementDialog.value) {
        // 如果对话框已经打开，更新标题
        const dialogEl = document.querySelector(".el-dialog__title");
        if (dialogEl) {
          dialogEl.textContent = "编辑配置";
        }
      }
    }, 0);
  };

  return {
    isEditMode,
    configs,
    activeConfigId,
    isShowConfigManagementDialog,
    configManagementForm,
    fetchAllConfigs,
    isSaveButtonDisabled,
    handleConfigSelect, isDeleteButtonDisabled,
    handleSaveConfig,
    handleDeleteConfig,
    handleNewConfig // 添加这行
  };
};
