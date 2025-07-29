import React, { useState, useEffect } from "react";
import QRCode from "qrcode";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Chip,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Paper,
  Avatar,
  CircularProgress,
} from "@mui/material";
import {
  QrCode,
  Add,
  Edit,
  Delete,
  Download,
  Visibility,
  ContentCopy,
  Launch,
  Settings,
} from "@mui/icons-material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { formBuilderAPI, type FormQRCode } from "../../services/formBuilder";

interface QRCodeManagerProps {
  formId: number;
  formTitle: string;
}

interface QRCodeFormData {
  external_url: string;
  title: string;
  description: string;
  size: number;
  error_correction: string;
  border: number;
  background_color: string;
  foreground_color: string;
}

interface QuickQRData {
  url: string;
  qrCodeDataUrl: string;
}

const QRCodeManager: React.FC<QRCodeManagerProps> = ({ formId, formTitle }) => {
  const queryClient = useQueryClient();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQR, setEditingQR] = useState<FormQRCode | null>(null);
  const [formData, setFormData] = useState<QRCodeFormData>({
    external_url: "",
    title: "",
    description: "",
    size: 200,
    error_correction: "M",
    border: 4,
    background_color: "#000000",
    foreground_color: "#FFFFFF",
  });
  const [previewUrl, setPreviewUrl] = useState("");

  // Quick QR generation state
  const [quickQR, setQuickQR] = useState<QuickQRData | null>(null);
  const [quickQRUrl, setQuickQRUrl] = useState(
    `${window.location.origin}/forms/${formId}`
  );
  const [generatingQuickQR, setGeneratingQuickQR] = useState(false);

  const generateQuickQR = React.useCallback(async () => {
    console.log("generateQuickQR called with URL:", quickQRUrl);
    if (!quickQRUrl.trim()) {
      console.log("No URL provided, exiting");
      return;
    }

    setGeneratingQuickQR(true);
    console.log("Starting QR generation...");

    try {
      // Generate QR code using the qrcode library (client-side)
      console.log("Generating QR with qrcode library...");
      const qrCodeDataUrl = await QRCode.toDataURL(quickQRUrl, {
        width: 256,
        margin: 2,
        color: {
          dark: "#000000",
          light: "#FFFFFF",
        },
      });

      console.log(
        "QR generation successful, data URL length:",
        qrCodeDataUrl.length
      );
      console.log("Data URL preview:", qrCodeDataUrl.substring(0, 100) + "...");

      setQuickQR({
        url: quickQRUrl,
        qrCodeDataUrl: qrCodeDataUrl,
      });
    } catch (error) {
      console.error("Failed to generate QR code:", error);
      // Fallback to external API if client-side generation fails
      try {
        console.log("Trying fallback API...");
        const fallbackUrl = `https://api.qrserver.com/v1/create-qr-code/?size=256x256&data=${encodeURIComponent(
          quickQRUrl
        )}`;
        console.log("Fallback URL:", fallbackUrl);
        setQuickQR({
          url: quickQRUrl,
          qrCodeDataUrl: fallbackUrl,
        });
      } catch (fallbackError) {
        console.error("Fallback QR generation also failed:", fallbackError);
      }
    } finally {
      setGeneratingQuickQR(false);
      console.log("QR generation process completed");
    }
  }, [quickQRUrl]);

  // Auto-generate QR code on component mount for demo
  useEffect(() => {
    if (quickQRUrl && !quickQR) {
      generateQuickQR();
    }
  }, [quickQRUrl, quickQR, generateQuickQR]);

  // Fetch QR codes
  const { data: qrCodes, isLoading } = useQuery({
    queryKey: ["form-qr-codes", formId],
    queryFn: () => formBuilderAPI.getFormQRCodes(formId),
  });

  // Create QR code mutation
  const createQRMutation = useMutation({
    mutationFn: (data: QRCodeFormData) =>
      formBuilderAPI.createFormQRCode(formId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["form-qr-codes", formId] });
      handleCloseDialog();
    },
  });

  // Update QR code mutation
  const updateQRMutation = useMutation({
    mutationFn: ({
      qrId,
      data,
    }: {
      qrId: number;
      data: Partial<QRCodeFormData>;
    }) => formBuilderAPI.updateFormQRCode(formId, qrId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["form-qr-codes", formId] });
      handleCloseDialog();
    },
  });

  // Delete QR code mutation
  const deleteQRMutation = useMutation({
    mutationFn: (qrId: number) => formBuilderAPI.deleteFormQRCode(formId, qrId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["form-qr-codes", formId] });
    },
  });

  const handleOpenDialog = (qr?: FormQRCode) => {
    if (qr) {
      setEditingQR(qr);
      setFormData({
        external_url: qr.external_url,
        title: qr.title,
        description: qr.description || "",
        size: qr.settings.size,
        error_correction: qr.settings.error_correction,
        border: qr.settings.border,
        background_color: qr.settings.background_color,
        foreground_color: qr.settings.foreground_color,
      });
    } else {
      setEditingQR(null);
      setFormData({
        external_url: "",
        title: `QR Code for ${formTitle}`,
        description: "",
        size: 200,
        error_correction: "M",
        border: 4,
        background_color: "#000000",
        foreground_color: "#FFFFFF",
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingQR(null);
    setPreviewUrl("");
  };

  const handleSubmit = () => {
    // Ensure external_url is provided
    if (!formData.external_url?.trim()) {
      alert("Please provide a valid URL for the QR code");
      return;
    }

    const submitData = {
      ...formData,
      external_url: formData.external_url.trim(),
    };

    if (editingQR) {
      updateQRMutation.mutate({
        qrId: editingQR.id,
        data: submitData,
      });
    } else {
      createQRMutation.mutate(submitData);
    }
  };

  const handleDelete = (qrId: number) => {
    if (window.confirm("Are you sure you want to delete this QR code?")) {
      deleteQRMutation.mutate(qrId);
    }
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You might want to add a toast notification here
  };

  const handleDownloadQR = (qrCode: FormQRCode) => {
    const link = document.createElement("a");
    link.href = qrCode.qr_code_data;
    link.download = `${qrCode.title
      .replace(/[^a-z0-9]/gi, "_")
      .toLowerCase()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleQuickQRDownload = () => {
    if (quickQR) {
      const link = document.createElement("a");
      link.href = quickQR.qrCodeDataUrl;
      link.download = `qr_code_${formTitle
        .replace(/[^a-z0-9]/gi, "_")
        .toLowerCase()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const generatePreviewUrl = React.useCallback(() => {
    if (formData.external_url) {
      // This would typically call an API to generate a preview QR code
      setPreviewUrl(
        "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y0ZjRmNCIvPgogIDx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM2NjYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5RUiBDb2RlIFByZXZpZXc8L3RleHQ+Cjwvc3ZnPgo="
      );
    }
  }, [formData.external_url]);

  useEffect(() => {
    generatePreviewUrl();
  }, [formData.external_url, formData.size, generatePreviewUrl]);

  if (isLoading) {
    return <Typography>Loading QR codes...</Typography>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography
          variant="h6"
          sx={{ display: "flex", alignItems: "center", gap: 1 }}
        >
          <QrCode />
          QR Code Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Create QR Code
        </Button>
      </Box>

      {/* Quick QR Generation Section */}
      <Card
        sx={{
          mb: 3,
          border: "2px dashed",
          borderColor: "primary.main",
          bgcolor: "primary.50",
        }}
      >
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: "flex", alignItems: "center", gap: 1 }}
          >
            <QrCode color="primary" />
            Quick QR Generator
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Generate a QR code instantly for any URL. Perfect for quick sharing!
          </Typography>

          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Enter URL"
                placeholder={`${window.location.origin}/forms/${formId}`}
                value={quickQRUrl}
                onChange={(e) => setQuickQRUrl(e.target.value)}
                variant="outlined"
                helperText="Enter any URL to generate a QR code"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={generateQuickQR}
                disabled={!quickQRUrl.trim() || generatingQuickQR}
                startIcon={
                  generatingQuickQR ? (
                    <CircularProgress size={20} />
                  ) : (
                    <QrCode />
                  )
                }
                sx={{ height: 56 }}
              >
                {generatingQuickQR ? "Generating..." : "Generate QR"}
              </Button>
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  console.log("Manual test button clicked");
                  setQuickQR(null);
                  generateQuickQR();
                }}
                disabled={generatingQuickQR}
                sx={{ height: 56 }}
              >
                Test QR
              </Button>
            </Grid>
            {quickQR && (
              <Grid item xs={12} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  onClick={handleQuickQRDownload}
                  startIcon={<Download />}
                  sx={{ height: 56 }}
                >
                  Download
                </Button>
              </Grid>
            )}
          </Grid>

          {/* QR Generation Status */}
          {generatingQuickQR && (
            <Box sx={{ mt: 2, textAlign: "center" }}>
              <CircularProgress size={24} />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Generating QR Code...
              </Typography>
            </Box>
          )}

          {quickQR && (
            <Box sx={{ mt: 3, textAlign: "center" }}>
              <Card variant="outlined" sx={{ display: "inline-block", p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Generated QR Code:
                </Typography>
                <Box
                  component="img"
                  src={quickQR.qrCodeDataUrl}
                  alt="Generated QR Code"
                  sx={{
                    width: 200,
                    height: 200,
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 1,
                    display: "block",
                    margin: "0 auto",
                  }}
                  onError={(e) => {
                    console.error("QR Code image failed to load:", e);
                    console.log("Image src:", quickQR.qrCodeDataUrl);
                  }}
                  onLoad={() => {
                    console.log("QR Code image loaded successfully");
                  }}
                />
                <Typography
                  variant="caption"
                  display="block"
                  sx={{ mt: 1, wordBreak: "break-all" }}
                >
                  URL: {quickQR.url}
                </Typography>
                <Typography
                  variant="caption"
                  display="block"
                  sx={{
                    mt: 0.5,
                    wordBreak: "break-all",
                    color: "text.secondary",
                  }}
                >
                  Source: {quickQR.qrCodeDataUrl}
                </Typography>
              </Card>
            </Box>
          )}

          {/* Debug Info */}
          <Box sx={{ mt: 2, p: 2, bgcolor: "grey.100", borderRadius: 1 }}>
            <Typography variant="caption" display="block">
              Debug Info:
            </Typography>
            <Typography variant="caption" display="block">
              quickQRUrl: {quickQRUrl}
            </Typography>
            <Typography variant="caption" display="block">
              generatingQuickQR: {generatingQuickQR.toString()}
            </Typography>
            <Typography variant="caption" display="block">
              quickQR exists: {quickQR ? "Yes" : "No"}
            </Typography>
            {quickQR && (
              <Typography variant="caption" display="block">
                QR Data URL length: {quickQR.qrCodeDataUrl.length}
              </Typography>
            )}
          </Box>
        </CardContent>
      </Card>

      {qrCodes?.qr_codes.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <QrCode sx={{ fontSize: 64, color: "gray", mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No QR Codes Created Yet
          </Typography>
          <Typography color="text.secondary" paragraph>
            Create QR codes to share your forms easily. Users can scan the code
            to access the form directly.
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => handleOpenDialog()}
          >
            Create Your First QR Code
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {qrCodes?.qr_codes.map((qr) => (
            <Grid item xs={12} md={6} lg={4} key={qr.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <Avatar sx={{ mr: 2, bgcolor: "primary.main" }}>
                      <QrCode />
                    </Avatar>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" noWrap>
                        {qr.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Created: {new Date(qr.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>

                  {qr.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      paragraph
                    >
                      {qr.description}
                    </Typography>
                  )}

                  <Box sx={{ textAlign: "center", mb: 2 }}>
                    <Box
                      component="img"
                      src={qr.qr_code_data}
                      alt={qr.title}
                      sx={{ maxWidth: "150px", height: "auto" }}
                    />
                  </Box>

                  <Box
                    sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}
                  >
                    <Chip
                      icon={<Visibility />}
                      label={`${qr.scan_count} scans`}
                      size="small"
                    />
                    <Chip
                      label={`${qr.settings.size}px`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={qr.settings.error_correction}
                      size="small"
                      variant="outlined"
                    />
                  </Box>

                  <TextField
                    fullWidth
                    size="small"
                    value={qr.external_url}
                    InputProps={{
                      readOnly: true,
                      endAdornment: (
                        <IconButton
                          size="small"
                          onClick={() => handleCopyToClipboard(qr.external_url)}
                        >
                          <ContentCopy />
                        </IconButton>
                      ),
                    }}
                    sx={{ mb: 2 }}
                  />
                </CardContent>

                <CardActions>
                  <Button
                    size="small"
                    startIcon={<Download />}
                    onClick={() => handleDownloadQR(qr)}
                  >
                    Download
                  </Button>
                  <Button
                    size="small"
                    startIcon={<Edit />}
                    onClick={() => handleOpenDialog(qr)}
                  >
                    Edit
                  </Button>
                  <Button
                    size="small"
                    startIcon={<Launch />}
                    onClick={() => window.open(qr.external_url, "_blank")}
                  >
                    Open
                  </Button>
                  <IconButton
                    size="small"
                    onClick={() => handleDelete(qr.id)}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* QR Code Creation/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingQR ? "Edit QR Code" : "Create New QR Code"}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="External URL *"
                value={formData.external_url}
                onChange={(e) =>
                  setFormData({ ...formData, external_url: e.target.value })
                }
                margin="normal"
                placeholder="https://example.com/your-form"
                helperText="The URL that the QR code will link to"
              />

              <TextField
                fullWidth
                label="Title *"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                margin="normal"
              />

              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                margin="normal"
                multiline
                rows={3}
              />

              <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
                <Settings sx={{ mr: 1 }} />
                QR Code Settings
              </Typography>

              <Typography gutterBottom>Size: {formData.size}px</Typography>
              <Slider
                value={formData.size}
                onChange={(_, value) =>
                  setFormData({ ...formData, size: value as number })
                }
                min={100}
                max={500}
                step={50}
                marks
                valueLabelDisplay="auto"
              />

              <FormControl fullWidth margin="normal">
                <InputLabel>Error Correction</InputLabel>
                <Select
                  value={formData.error_correction}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      error_correction: e.target.value,
                    })
                  }
                  label="Error Correction"
                >
                  <MenuItem value="L">Low (7%)</MenuItem>
                  <MenuItem value="M">Medium (15%)</MenuItem>
                  <MenuItem value="Q">Quartile (25%)</MenuItem>
                  <MenuItem value="H">High (30%)</MenuItem>
                </Select>
              </FormControl>

              <Typography gutterBottom sx={{ mt: 2 }}>
                Border: {formData.border}px
              </Typography>
              <Slider
                value={formData.border}
                onChange={(_, value) =>
                  setFormData({ ...formData, border: value as number })
                }
                min={0}
                max={10}
                step={1}
                marks
                valueLabelDisplay="auto"
              />

              <Grid container spacing={2} sx={{ mt: 2 }}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Background Color"
                    type="color"
                    value={formData.background_color}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        background_color: e.target.value,
                      })
                    }
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Foreground Color"
                    type="color"
                    value={formData.foreground_color}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        foreground_color: e.target.value,
                      })
                    }
                  />
                </Grid>
              </Grid>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Preview
              </Typography>

              {previewUrl ? (
                <Box
                  sx={{
                    textAlign: "center",
                    p: 2,
                    border: "1px dashed #ccc",
                    borderRadius: 1,
                  }}
                >
                  <Box
                    component="img"
                    src={previewUrl}
                    alt="QR Code Preview"
                    sx={{ maxWidth: "100%", height: "auto" }}
                  />
                  <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                    Preview QR Code
                  </Typography>
                </Box>
              ) : (
                <Box
                  sx={{
                    textAlign: "center",
                    p: 4,
                    border: "1px dashed #ccc",
                    borderRadius: 1,
                  }}
                >
                  <QrCode sx={{ fontSize: 64, color: "gray" }} />
                  <Typography variant="caption" display="block">
                    Enter a URL to see preview
                  </Typography>
                </Box>
              )}

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Tips:</strong>
                  <br />• Higher error correction allows the QR code to work
                  even if partially damaged
                  <br />• Larger sizes are easier to scan from a distance
                  <br />• Use high contrast colors for better readability
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.external_url ||
              !formData.title ||
              createQRMutation.isPending ||
              updateQRMutation.isPending
            }
          >
            {editingQR ? "Update" : "Create"} QR Code
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QRCodeManager;
