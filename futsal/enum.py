from enum import Enum

class ImageType(Enum):
    PICTURE = "Picture"
    DOCUMENT = "Document"

class VenueApprovalStatus(Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    
