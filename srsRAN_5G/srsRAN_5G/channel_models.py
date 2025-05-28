import math
import random
from abc import ABC, abstractmethod

class Position:
    """Represents a position in a 2D plane."""
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def distance_to(self, other):
        """Return the Euclidean distance to another position."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __str__(self):
        return f"({self.x:.2f}, {self.y:.2f})"


class ChannelModel(ABC):
    """Abstract base class for channel models."""

    @abstractmethod
    def calculate_rsrp(self, gnb, ue_position):
        """Calculate RSRP of a UE relative to a gNB."""
        pass

    @abstractmethod
    def calculate_sinr(self, gnb, ue_position, interfering_gnbs):
        """Calculate SINR of a UE relative to a gNB."""
        pass

    @abstractmethod
    def is_in_coverage(self, gnb, ue_position, threshold=-110):
        """Check whether the UE is within gNB coverage."""
        pass


class SimplifiedChannelModel(ChannelModel):
    """Simple pathloss based channel model with random fading."""

    def calculate_rsrp(self, gnb, ue_position):
        distance_km = gnb.position.distance_to(ue_position) / 1000.0
        if distance_km < 0.001:
            distance_km = 0.001
        try:
            path_loss = 32.4 + 20 * math.log10(gnb.frequency) + 20 * math.log10(distance_km)
        except ValueError:
            return -float("inf")
        fading = random.uniform(0, 5)
        return gnb.power - path_loss - fading

    def calculate_sinr(self, gnb, ue_position, interfering_gnbs):
        signal_power_linear = 10 ** (self.calculate_rsrp(gnb, ue_position) / 10.0)
        interference_power_linear = 0.0
        for interfering_gnb in interfering_gnbs:
            if interfering_gnb != gnb:
                interference_power_linear += 10 ** (
                    self.calculate_rsrp(interfering_gnb, ue_position) / 10.0
                )
        noise_power_linear = 10 ** (-100 / 10.0)
        if interference_power_linear + noise_power_linear == 0:
            return float("inf")
        sinr_linear = signal_power_linear / (interference_power_linear + noise_power_linear)
        try:
            return 10 * math.log10(sinr_linear)
        except ValueError:
            return -float("inf")

    def is_in_coverage(self, gnb, ue_position, threshold=-110):
        rsrp = self.calculate_rsrp(gnb, ue_position)
        return rsrp >= threshold


class ExternalChannelModelPlaceholder(ChannelModel):
    """Placeholder for integration with an external channel simulator."""

    def __init__(self, external_simulator_api=None):
        self.api = external_simulator_api
        print(
            "Using External Channel Model Placeholder. Implement integration with your simulator."
        )

    def calculate_rsrp(self, gnb, ue_position):
        if self.api:
            pass
        simplified_model = SimplifiedChannelModel()
        return simplified_model.calculate_rsrp(gnb, ue_position)

    def calculate_sinr(self, gnb, ue_position, interfering_gnbs):
        if self.api:
            pass
        simplified_model = SimplifiedChannelModel()
        return simplified_model.calculate_sinr(gnb, ue_position, interfering_gnbs)

    def is_in_coverage(self, gnb, ue_position, threshold=-110):
        if self.api:
            pass
        simplified_model = SimplifiedChannelModel()
        return simplified_model.is_in_coverage(gnb, ue_position, threshold)
