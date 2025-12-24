//////////////////////////////////////////////////////////////////////////////
//
// Copyright 2025 Autodesk, Inc. All rights reserved.
//
// Use of this software is subject to the terms of the Autodesk license
// agreement provided at the time of installation or download, or which
// otherwise accompanies this software.
//
//////////////////////////////////////////////////////////////////////////////

#pragma once

namespace adsk { namespace sim {

/// Simulation constraint types.
enum ConstraintTypes
{
    /// Unknown constraint type.
    UnknownConstraintType,
    /// Fixed constraint type.
    FixedConstraintType,
    /// Surface roller constraint type.
    SurfaceRollerConstraintType,
    /// Directional constraint type.
    DirectionalConstraintType,
    /// Pin constraint type.
    PinConstraintType,
    /// Remote constraint type.
    RemoteConstraintType
};

/// Load direction types.
enum LoadDirectionTypes
{
    /// Unknown load direction type.
    UnknownLoadDirectionType,
    /// Load direction type default.
    DefaultLoadDirectionType,
    /// Load direction type cartesian.
    CartesianLoadDirectionType,
    /// Load direction type angles.
    AnglesLoadDirectionType,
    /// Load direction type reference.
    ReferenceLoadDirectionType
};

/// Simulation study types.
enum StudyTypes
{
    /// Unknown study type.
    UnknownStudyType,
    /// Structural linear static stress simulation study type.
    LinearStaticStressStudyType,
    /// Structural nonlinear static stress simulation study type.
    NonLinearStaticStressStudyType,
    /// Structural dynamic event simulation study type.
    DynamicEventSimulationStudyType
};

}// namespace sim
}// namespace adsk
